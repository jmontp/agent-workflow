#!/usr/bin/env python3
"""
Deep Browser Cache Analysis Tool

This tool performs advanced analysis of browser caching issues that persist
despite proper cache-busting headers, focusing on edge cases and browser-specific
caching behaviors that may cause interfaces to show old content.
"""

import os
import sys
import json
import time
import requests
import hashlib
import threading
from pathlib import Path
from datetime import datetime
import webbrowser
import tempfile
import html

class DeepCacheAnalyzer:
    """Advanced browser cache analysis for persistent cache issues"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "analysis_time": datetime.now().isoformat(),
            "browser_specific_issues": {},
            "javascript_execution_issues": {},
            "resource_dependency_issues": {},
            "timing_issues": {},
            "memory_cache_issues": {},
            "recommendations": []
        }
        
    def analyze_javascript_execution_order(self):
        """Analyze JavaScript execution order and dependencies"""
        print("🔍 Analyzing JavaScript execution order...")
        
        try:
            response = requests.get(self.base_url, timeout=5)
            html_content = response.text
            
            # Extract all script tags in order
            import re
            script_pattern = r'<script[^>]*src=["\']([^"\']*)["\'][^>]*>'
            scripts = re.findall(script_pattern, html_content)
            
            # Categorize scripts
            external_scripts = [s for s in scripts if s.startswith('http')]
            local_scripts = [s for s in scripts if not s.startswith('http')]
            
            # Check for potential dependency issues
            critical_scripts = [
                'socket.io.min.js',  # Must load before local scripts
                'mermaid.min.js',    # Must load before visualizer
                'chat-components.js', # Must load before discord-chat.js
                'discord-chat.js',   # Must load before chat-init-failsafe.js
                'visualizer.js',     # Core visualizer
                'chat-init-failsafe.js'  # Last resort initialization
            ]
            
            execution_analysis = {
                "external_first": external_scripts,
                "local_scripts": local_scripts,
                "total_scripts": len(scripts),
                "potential_race_conditions": [],
                "dependency_order_issues": []
            }
            
            # Check for race conditions
            if 'chat-components.js' in str(local_scripts) and 'discord-chat.js' in str(local_scripts):
                chat_comp_idx = None
                discord_chat_idx = None
                
                for i, script in enumerate(local_scripts):
                    if 'chat-components.js' in script:
                        chat_comp_idx = i
                    elif 'discord-chat.js' in script:
                        discord_chat_idx = i
                        
                if chat_comp_idx is not None and discord_chat_idx is not None:
                    if chat_comp_idx > discord_chat_idx:
                        execution_analysis["dependency_order_issues"].append({
                            "issue": "chat-components.js loads after discord-chat.js",
                            "impact": "Discord chat may fail to initialize properly",
                            "severity": "high"
                        })
                        
            # Check for too many scripts (browser connection limit)
            if len(local_scripts) > 6:
                execution_analysis["potential_race_conditions"].append({
                    "issue": f"Too many local scripts ({len(local_scripts)})",
                    "impact": "May exceed browser connection limits, causing random load failures",
                    "severity": "medium"
                })
                
            self.results["javascript_execution_issues"] = execution_analysis
            
            print(f"  📄 Found {len(scripts)} total scripts")
            print(f"  🌐 External: {len(external_scripts)}")
            print(f"  🏠 Local: {len(local_scripts)}")
            
            if execution_analysis["dependency_order_issues"]:
                print(f"  ⚠️ {len(execution_analysis['dependency_order_issues'])} dependency issues found")
                
        except Exception as e:
            self.results["javascript_execution_issues"] = {"error": str(e)}
            print(f"  ❌ Error analyzing JavaScript execution: {e}")
            
    def test_resource_loading_timing(self):
        """Test for timing-related resource loading issues"""
        print("🔍 Testing resource loading timing...")
        
        # Test multiple concurrent requests to simulate browser behavior
        test_urls = [
            f"{self.base_url}/static/visualizer.js",
            f"{self.base_url}/static/js/chat-components.js",
            f"{self.base_url}/static/js/discord-chat.js",
            f"{self.base_url}/static/css/discord-chat.css"
        ]
        
        timing_results = {}
        
        for i in range(3):  # Test 3 times
            print(f"  🔄 Test round {i+1}/3")
            
            # Concurrent requests
            def fetch_resource(url):
                try:
                    start = time.time()
                    response = requests.get(url, timeout=5)
                    end = time.time()
                    return {
                        "url": url,
                        "status": response.status_code,
                        "time": round((end - start) * 1000, 2),
                        "size": len(response.content),
                        "hash": hashlib.sha256(response.content).hexdigest()[:16]
                    }
                except Exception as e:
                    return {"url": url, "error": str(e)}
                    
            threads = []
            results = []
            
            for url in test_urls:
                thread = threading.Thread(target=lambda u=url: results.append(fetch_resource(u)))
                threads.append(thread)
                thread.start()
                
            for thread in threads:
                thread.join()
                
            timing_results[f"round_{i+1}"] = results
            time.sleep(1)  # Brief pause between rounds
            
        # Analyze timing consistency
        timing_analysis = {
            "rounds": timing_results,
            "consistency_issues": [],
            "performance_issues": []
        }
        
        # Check for inconsistent response times
        for url in test_urls:
            times = []
            hashes = []
            
            for round_name, round_results in timing_results.items():
                for result in round_results:
                    if result.get("url") == url and "time" in result:
                        times.append(result["time"])
                        hashes.append(result.get("hash"))
                        
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                # Check for high variance (>50% difference)
                if max_time > min_time * 1.5:
                    timing_analysis["consistency_issues"].append({
                        "resource": url.split("/")[-1],
                        "min_time": min_time,
                        "max_time": max_time,
                        "variance": round(((max_time - min_time) / min_time) * 100, 1),
                        "impact": "Inconsistent loading may cause race conditions"
                    })
                    
                # Check for slow resources (>500ms)
                if avg_time > 500:
                    timing_analysis["performance_issues"].append({
                        "resource": url.split("/")[-1],
                        "avg_time": round(avg_time, 2),
                        "impact": "Slow loading may cause initialization failures"
                    })
                    
            # Check for content inconsistency
            if len(set(hashes)) > 1:
                timing_analysis["consistency_issues"].append({
                    "resource": url.split("/")[-1],
                    "issue": "Content hash varies between requests",
                    "impact": "Resource content is changing during testing",
                    "severity": "critical"
                })
                
        self.results["timing_issues"] = timing_analysis
        
        if timing_analysis["consistency_issues"]:
            print(f"  ⚠️ {len(timing_analysis['consistency_issues'])} timing consistency issues")
        if timing_analysis["performance_issues"]:
            print(f"  🐌 {len(timing_analysis['performance_issues'])} performance issues")
        if not timing_analysis["consistency_issues"] and not timing_analysis["performance_issues"]:
            print("  ✅ Resource loading timing appears consistent")
            
    def analyze_memory_cache_behavior(self):
        """Analyze browser memory cache behavior"""
        print("🔍 Analyzing memory cache behavior...")
        
        # Test same resource with different cache-busting strategies
        base_url = f"{self.base_url}/static/visualizer.js"
        
        cache_strategies = {
            "normal": base_url,
            "timestamp": f"{base_url}?t={int(time.time())}",
            "random": f"{base_url}?r={hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
            "version": f"{base_url}?v=1.0.0",
            "cache_buster": f"{base_url}?cb={int(time.time() * 1000)}",
            "no_cache_param": f"{base_url}?no-cache=true"
        }
        
        memory_test_results = {}
        
        for strategy_name, url in cache_strategies.items():
            try:
                # First request
                start1 = time.time()
                resp1 = requests.get(url, timeout=5)
                end1 = time.time()
                
                # Immediate second request (should hit memory cache if caching enabled)
                start2 = time.time()
                resp2 = requests.get(url, timeout=5)
                end2 = time.time()
                
                time1 = round((end1 - start1) * 1000, 2)
                time2 = round((end2 - start2) * 1000, 2)
                
                memory_test_results[strategy_name] = {
                    "first_request_ms": time1,
                    "second_request_ms": time2,
                    "time_difference": round(time1 - time2, 2),
                    "likely_cached": time2 < time1 * 0.5,  # 50% faster = likely cached
                    "content_identical": resp1.content == resp2.content,
                    "headers_identical": dict(resp1.headers) == dict(resp2.headers)
                }
                
                print(f"  📊 {strategy_name}: {time1}ms → {time2}ms ({'cached' if memory_test_results[strategy_name]['likely_cached'] else 'not cached'})")
                
            except Exception as e:
                memory_test_results[strategy_name] = {"error": str(e)}
                print(f"  ❌ {strategy_name}: {e}")
                
        # Analyze results
        memory_analysis = {
            "test_results": memory_test_results,
            "cache_behavior_issues": [],
            "recommendations": []
        }
        
        # Check if any strategy shows unexpected caching
        for strategy, result in memory_test_results.items():
            if "error" not in result:
                if result["likely_cached"] and strategy != "normal":
                    memory_analysis["cache_behavior_issues"].append({
                        "strategy": strategy,
                        "issue": "Cache busting strategy not effective",
                        "first_time": result["first_request_ms"],
                        "second_time": result["second_request_ms"],
                        "impact": "Browser may be serving cached content despite cache busting"
                    })
                    
        # Check for content inconsistency
        normal_result = memory_test_results.get("normal", {})
        for strategy, result in memory_test_results.items():
            if strategy != "normal" and "error" not in result and "error" not in normal_result:
                if not result.get("content_identical", True):
                    memory_analysis["cache_behavior_issues"].append({
                        "strategy": strategy,
                        "issue": "Content differs from normal request",
                        "impact": "Resource serving is inconsistent",
                        "severity": "critical"
                    })
                    
        self.results["memory_cache_issues"] = memory_analysis
        
        if memory_analysis["cache_behavior_issues"]:
            print(f"  ⚠️ {len(memory_analysis['cache_behavior_issues'])} memory cache issues found")
        else:
            print("  ✅ Memory cache behavior appears correct")
            
    def create_browser_test_page(self):
        """Create a test page to diagnose browser-specific issues"""
        print("🔧 Creating browser test page...")
        
        test_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Cache Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .test-section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .result {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            font-family: monospace;
        }}
        .success {{ background: #d4edda; color: #155724; }}
        .error {{ background: #f8d7da; color: #721c24; }}
        .warning {{ background: #fff3cd; color: #856404; }}
        .info {{ background: #d1ecf1; color: #0c5460; }}
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }}
        button:hover {{ background: #0056b3; }}
        #progress {{ margin: 20px 0; }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: #28a745;
            width: 0%;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <h1>🔍 Deep Browser Cache Analysis</h1>
    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="test-section">
        <h2>🚀 Automated Tests</h2>
        <button onclick="runAllTests()">Run All Tests</button>
        <button onclick="clearAllCaches()">Clear All Caches</button>
        <button onclick="testResourceLoading()">Test Resource Loading</button>
        <button onclick="testJavaScriptExecution()">Test JavaScript Execution</button>
        
        <div id="progress">
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <div id="progress-text">Ready to run tests</div>
        </div>
        
        <div id="test-results"></div>
    </div>
    
    <div class="test-section">
        <h2>🌐 Browser Information</h2>
        <div id="browser-info"></div>
    </div>
    
    <div class="test-section">
        <h2>📊 Resource Loading Analysis</h2>
        <div id="resource-analysis"></div>
    </div>
    
    <div class="test-section">
        <h2>💾 Cache Status</h2>
        <div id="cache-status"></div>
    </div>
    
    <script>
        const testResults = document.getElementById('test-results');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        let testProgress = 0;
        
        function updateProgress(percent, text) {{
            progressFill.style.width = percent + '%';
            progressText.textContent = text;
        }}
        
        function addResult(message, type = 'info') {{
            const div = document.createElement('div');
            div.className = `result ${{type}}`;
            div.textContent = new Date().toLocaleTimeString() + ': ' + message;
            testResults.appendChild(div);
            testResults.scrollTop = testResults.scrollHeight;
        }}
        
        function getBrowserInfo() {{
            const info = {{
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                cookieEnabled: navigator.cookieEnabled,
                onLine: navigator.onLine,
                hardwareConcurrency: navigator.hardwareConcurrency,
                maxTouchPoints: navigator.maxTouchPoints,
                serviceWorker: 'serviceWorker' in navigator,
                localStorage: typeof(Storage) !== 'undefined',
                sessionStorage: typeof(Storage) !== 'undefined',
                indexedDB: 'indexedDB' in window,
                webSQL: 'openDatabase' in window,
                applicationCache: 'applicationCache' in window,
                caches: 'caches' in window,
                currentTime: new Date().toISOString(),
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                screen: {{
                    width: screen.width,
                    height: screen.height,
                    colorDepth: screen.colorDepth
                }}
            }};
            
            document.getElementById('browser-info').innerHTML = 
                Object.entries(info).map(([key, value]) => 
                    `<strong>${{key}}:</strong> ${{typeof value === 'object' ? JSON.stringify(value) : value}}`
                ).join('<br>');
        }}
        
        async function clearAllCaches() {{
            addResult('Starting cache clearing process...', 'info');
            
            try {{
                // Clear service worker caches
                if ('caches' in window) {{
                    const cacheNames = await caches.keys();
                    for (const cacheName of cacheNames) {{
                        await caches.delete(cacheName);
                        addResult(`Deleted cache: ${{cacheName}}`, 'success');
                    }}
                }}
                
                // Clear storage
                if (localStorage) {{
                    localStorage.clear();
                    addResult('Cleared localStorage', 'success');
                }}
                
                if (sessionStorage) {{
                    sessionStorage.clear();
                    addResult('Cleared sessionStorage', 'success');
                }}
                
                addResult('All caches cleared successfully!', 'success');
                
            }} catch (error) {{
                addResult(`Error clearing caches: ${{error.message}}`, 'error');
            }}
        }}
        
        async function testResourceLoading() {{
            addResult('Testing resource loading...', 'info');
            
            const testUrls = [
                '{self.base_url}/static/visualizer.js',
                '{self.base_url}/static/js/chat-components.js',
                '{self.base_url}/static/js/discord-chat.js',
                '{self.base_url}/static/css/discord-chat.css'
            ];
            
            const results = [];
            
            for (const url of testUrls) {{
                try {{
                    const startTime = performance.now();
                    const response = await fetch(url + '?t=' + Date.now());
                    const endTime = performance.now();
                    
                    const resourceName = url.split('/').pop();
                    const loadTime = Math.round(endTime - startTime);
                    
                    if (response.ok) {{
                        addResult(`✅ ${{resourceName}}: ${{response.status}} (${{loadTime}}ms)`, 'success');
                        results.push({{ url, status: response.status, loadTime, size: response.headers.get('content-length') }});
                    }} else {{
                        addResult(`❌ ${{resourceName}}: ${{response.status}} (${{loadTime}}ms)`, 'error');
                    }}
                    
                }} catch (error) {{
                    addResult(`❌ ${{url.split('/').pop()}}: ${{error.message}}`, 'error');
                }}
            }}
            
            document.getElementById('resource-analysis').innerHTML = 
                '<h3>Resource Loading Results:</h3>' +
                results.map(r => `<div>${{r.url.split('/').pop()}}: ${{r.status}} (${{r.loadTime}}ms, ${{r.size || 'unknown'}} bytes)</div>`).join('');
        }}
        
        async function testJavaScriptExecution() {{
            addResult('Testing JavaScript execution environment...', 'info');
            
            const tests = [
                {{ name: 'Socket.IO', test: () => typeof io !== 'undefined' }},
                {{ name: 'Mermaid', test: () => typeof mermaid !== 'undefined' }},
                {{ name: 'Visualizer', test: () => typeof window.visualizer !== 'undefined' }},
                {{ name: 'Discord Chat', test: () => typeof window.discordChat !== 'undefined' }},
                {{ name: 'Chat Components', test: () => typeof window.chatComponents !== 'undefined' }},
            ];
            
            for (const {{ name, test }} of tests) {{
                try {{
                    const result = test();
                    addResult(`${{result ? '✅' : '❌'}} ${{name}}: ${{result ? 'Available' : 'Not found'}}`, result ? 'success' : 'warning');
                }} catch (error) {{
                    addResult(`❌ ${{name}}: Error - ${{error.message}}`, 'error');
                }}
            }}
            
            // Test specific functionality
            try {{
                const input = document.getElementById('chat-input-field');
                const button = document.getElementById('chat-send-btn');
                
                if (input && button) {{
                    addResult('✅ Chat elements found in parent window', 'success');
                    addResult(`Button disabled: ${{window.parent.document.getElementById('chat-send-btn')?.disabled}}`, 'info');
                }} else {{
                    addResult('❌ Chat elements not found - opening parent window for testing', 'warning');
                    // Try to test parent window
                    try {{
                        const parentInput = window.parent.document.getElementById('chat-input-field');
                        const parentButton = window.parent.document.getElementById('chat-send-btn');
                        
                        if (parentInput && parentButton) {{
                            addResult('✅ Chat elements found in parent window', 'success');
                            addResult(`Parent button disabled: ${{parentButton.disabled}}`, 'info');
                            
                            // Test input event
                            parentInput.value = 'Test';
                            parentInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                            
                            setTimeout(() => {{
                                addResult(`After test input - Button disabled: ${{parentButton.disabled}}`, parentButton.disabled ? 'error' : 'success');
                            }}, 100);
                            
                        }} else {{
                            addResult('❌ Chat elements not found in parent window either', 'error');
                        }}
                    }} catch (e) {{
                        addResult(`Cannot access parent window: ${{e.message}}`, 'warning');
                    }}
                }}
            }} catch (error) {{
                addResult(`Error testing chat functionality: ${{error.message}}`, 'error');
            }}
        }}
        
        async function runAllTests() {{
            addResult('Starting comprehensive cache analysis...', 'info');
            updateProgress(0, 'Starting tests...');
            
            updateProgress(10, 'Getting browser info...');
            getBrowserInfo();
            
            updateProgress(30, 'Clearing caches...');
            await clearAllCaches();
            
            updateProgress(60, 'Testing resource loading...');
            await testResourceLoading();
            
            updateProgress(90, 'Testing JavaScript execution...');
            await testJavaScriptExecution();
            
            updateProgress(100, 'Tests completed!');
            addResult('All tests completed!', 'success');
        }}
        
        // Initialize
        getBrowserInfo();
        
        // Auto-run tests after 2 seconds
        setTimeout(() => {{
            addResult('Auto-running tests in 2 seconds...', 'info');
            setTimeout(runAllTests, 2000);
        }}, 100);
    </script>
</body>
</html>'''
        
        test_file = Path(__file__).parent / "deep_cache_test.html"
        test_file.write_text(test_html)
        
        print(f"✅ Created browser test page: {test_file}")
        
        # Try to open in browser
        try:
            file_url = f"file://{test_file.absolute()}"
            webbrowser.open(file_url)
            print(f"🌐 Opening test page in browser: {file_url}")
        except Exception as e:
            print(f"ℹ️ Could not auto-open browser: {e}")
            print(f"   Please open manually: {test_file}")
            
        self.results["test_page"] = str(test_file)
        
    def generate_comprehensive_recommendations(self):
        """Generate comprehensive recommendations based on all findings"""
        print("💡 Generating comprehensive recommendations...")
        
        recommendations = []
        
        # JavaScript execution issues
        if self.results.get("javascript_execution_issues", {}).get("dependency_order_issues"):
            recommendations.append({
                "category": "JavaScript Dependencies",
                "priority": "HIGH",
                "issue": "Script loading order may cause initialization failures",
                "solution": "Reorder script tags to ensure dependencies load first",
                "implementation": "Move chat-components.js before discord-chat.js in HTML template"
            })
            
        # Timing issues
        timing_issues = self.results.get("timing_issues", {}).get("consistency_issues", [])
        if timing_issues:
            recommendations.append({
                "category": "Resource Loading Timing",
                "priority": "MEDIUM",
                "issue": f"Found {len(timing_issues)} timing consistency issues",
                "solution": "Implement resource loading queue and retry mechanism",
                "implementation": "Add loading indicators and retry logic for failed resources"
            })
            
        # Memory cache issues
        memory_issues = self.results.get("memory_cache_issues", {}).get("cache_behavior_issues", [])
        if memory_issues:
            recommendations.append({
                "category": "Memory Cache Behavior",
                "priority": "HIGH",
                "issue": f"Found {len(memory_issues)} cache behavior issues",
                "solution": "Implement stronger cache busting mechanisms",
                "implementation": "Use content-based hashing for cache busting instead of timestamps"
            })
            
        # General recommendations
        recommendations.extend([
            {
                "category": "Browser Compatibility",
                "priority": "HIGH",
                "issue": "Different browsers may handle caching differently",
                "solution": "Test with multiple browsers and implement browser-specific workarounds",
                "implementation": "Create browser detection and apply specific cache strategies"
            },
            {
                "category": "Development Workflow",
                "priority": "MEDIUM",
                "issue": "Cache issues persist despite cache-busting headers",
                "solution": "Implement development-specific cache busting",
                "implementation": "Add build timestamp or git hash to all resource URLs"
            },
            {
                "category": "Resource Bundling",
                "priority": "LOW",
                "issue": "Too many individual script files may cause loading issues",
                "solution": "Bundle JavaScript files to reduce HTTP requests",
                "implementation": "Use webpack or similar bundler for production builds"
            }
        ])
        
        self.results["recommendations"] = recommendations
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        
    def run_deep_analysis(self):
        """Run comprehensive deep cache analysis"""
        print("🚀 Starting deep browser cache analysis...")
        print("=" * 60)
        
        try:
            self.analyze_javascript_execution_order()
            self.test_resource_loading_timing()
            self.analyze_memory_cache_behavior()
            self.create_browser_test_page()
            self.generate_comprehensive_recommendations()
            
            return self.generate_final_report()
            
        except Exception as e:
            print(f"❌ Error during deep analysis: {e}")
            return {"error": str(e)}
            
    def generate_final_report(self):
        """Generate final comprehensive report"""
        print("\n" + "=" * 60)
        print("📊 DEEP BROWSER CACHE ANALYSIS REPORT")
        print("=" * 60)
        
        # Count issues
        js_issues = len(self.results.get("javascript_execution_issues", {}).get("dependency_order_issues", []))
        timing_issues = len(self.results.get("timing_issues", {}).get("consistency_issues", []))
        memory_issues = len(self.results.get("memory_cache_issues", {}).get("cache_behavior_issues", []))
        
        total_issues = js_issues + timing_issues + memory_issues
        
        print(f"\n📈 ANALYSIS SUMMARY:")
        print(f"  JavaScript Issues: {js_issues}")
        print(f"  Timing Issues: {timing_issues}")
        print(f"  Memory Cache Issues: {memory_issues}")
        print(f"  Total Issues: {total_issues}")
        
        if total_issues == 0:
            print(f"\n✅ NO DEEP CACHE ISSUES DETECTED")
            print(f"  The caching system appears to be working correctly.")
            print(f"  If you're still experiencing issues, they may be:")
            print(f"  1. Browser-specific behavior")
            print(f"  2. Extension interference")
            print(f"  3. Network proxy caching")
            print(f"  4. Application-level state issues")
        else:
            print(f"\n🚨 ISSUES DETECTED:")
            
            if js_issues:
                print(f"  🔧 JavaScript Dependency Issues:")
                for issue in self.results.get("javascript_execution_issues", {}).get("dependency_order_issues", []):
                    print(f"    • {issue['issue']} (Impact: {issue['impact']})")
                    
            if timing_issues:
                print(f"  ⏱️ Resource Loading Timing Issues:")
                for issue in self.results.get("timing_issues", {}).get("consistency_issues", []):
                    print(f"    • {issue.get('resource', 'Unknown')}: {issue.get('issue', 'Timing variance')}")
                    
            if memory_issues:
                print(f"  💾 Memory Cache Issues:")
                for issue in self.results.get("memory_cache_issues", {}).get("cache_behavior_issues", []):
                    print(f"    • {issue['strategy']}: {issue['issue']}")
                    
        # Show recommendations
        recommendations = self.results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 PRIORITIZED RECOMMENDATIONS:")
            
            high_priority = [r for r in recommendations if r.get("priority") == "HIGH"]
            medium_priority = [r for r in recommendations if r.get("priority") == "MEDIUM"]
            low_priority = [r for r in recommendations if r.get("priority") == "LOW"]
            
            for priority, recs in [("HIGH", high_priority), ("MEDIUM", medium_priority), ("LOW", low_priority)]:
                if recs:
                    print(f"\n  {priority} PRIORITY:")
                    for rec in recs:
                        print(f"    🔴 {rec['category']}: {rec['issue']}")
                        print(f"       💡 Solution: {rec['solution']}")
                        print(f"       🔧 Implementation: {rec['implementation']}")
                        
        print(f"\n📋 NEXT STEPS:")
        print(f"  1. Open the browser test page to run interactive tests")
        print(f"  2. Check browser console for JavaScript errors")
        print(f"  3. Test with different browsers (Chrome, Firefox, Edge)")
        print(f"  4. Try incognito/private browsing mode")
        print(f"  5. Disable browser extensions temporarily")
        
        if self.results.get("test_page"):
            print(f"\n🌐 INTERACTIVE TEST PAGE:")
            print(f"  File: {self.results['test_page']}")
            print(f"  This page will help diagnose browser-specific issues")
            
        # Save detailed report
        report_path = Path(__file__).parent / f"deep_cache_analysis_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved: {report_path}")
        
        return self.results

def main():
    """Main entry point"""
    print("🔍 Deep Browser Cache Analysis Tool") 
    print("=" * 50)
    print("This tool analyzes complex browser caching issues that")
    print("persist despite proper cache-busting headers.")
    print()
    
    analyzer = DeepCacheAnalyzer()
    results = analyzer.run_deep_analysis()
    
    print(f"\n🎯 Deep analysis complete!")
    print(f"Use the generated test page for interactive browser testing.")
    
    return results

if __name__ == "__main__":
    main()