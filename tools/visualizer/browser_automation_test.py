#!/usr/bin/env python3
"""
Browser-based UI Test Runner

Uses JavaScript injection to test UI functionality from within the browser.
This script generates a test HTML page that can be opened in any browser
to automatically detect UI errors.
"""

import json
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class BrowserAutomationTest:
    """Generate browser-based UI tests"""
    
    def __init__(self, port: int = 5000):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.test_file = None
        
    def generate_test_html(self) -> str:
        """Generate the test HTML file"""
        test_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Error Detection Test</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }}
        .test-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .test-results {{
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }}
        .test-result {{
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
        }}
        .test-result.pass {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .test-result.fail {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .test-result.error {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .iframe-container {{
            width: 100%;
            height: 600px;
            border: 2px solid #ddd;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .iframe-container iframe {{
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 4px;
        }}
        .control-panel {{
            margin: 20px 0;
            padding: 15px;
            background: #e9ecef;
            border-radius: 4px;
        }}
        .control-panel button {{
            margin: 5px;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .control-panel button.primary {{
            background: #007bff;
            color: white;
        }}
        .control-panel button.secondary {{
            background: #6c757d;
            color: white;
        }}
        .log-container {{
            background: #000;
            color: #0f0;
            padding: 15px;
            border-radius: 4px;
            height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }}
        .summary {{
            margin: 20px 0;
            padding: 15px;
            background: #e7f3ff;
            border-radius: 4px;
        }}
        .summary h3 {{
            margin-top: 0;
        }}
        .test-details {{
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 14px;
        }}
        .screenshot {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .error-highlight {{
            background: #ffeb3b;
            padding: 2px 4px;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div class="test-container">
        <h1>🔍 UI Error Detection Test Suite</h1>
        <p>This page automatically tests the web interface for common UI errors.</p>
        
        <div class="control-panel">
            <button class="primary" onclick="startTests()">🚀 Start Tests</button>
            <button class="secondary" onclick="reloadInterface()">🔄 Reload Interface</button>
            <button class="secondary" onclick="takeScreenshot()">📸 Screenshot</button>
            <button class="secondary" onclick="exportResults()">💾 Export Results</button>
            <button class="secondary" onclick="clearLog()">🗑️ Clear Log</button>
        </div>
        
        <div class="iframe-container">
            <iframe id="testIframe" src="{self.base_url}" title="Web Interface Under Test"></iframe>
        </div>
        
        <div class="summary" id="testSummary" style="display: none;">
            <h3>Test Summary</h3>
            <div id="summaryContent"></div>
        </div>
        
        <div class="test-results" id="testResults">
            <h3>Test Results</h3>
            <div id="resultsContent">
                <p>Click "Start Tests" to begin automated error detection.</p>
            </div>
        </div>
        
        <div class="log-container" id="logContainer">
            <div id="logContent">UI Error Detection Test Suite Ready</div>
        </div>
    </div>
    
    <script>
        let testResults = [];
        let testStartTime = null;
        let testIframe = null;
        
        function log(message, type = 'info') {{
            const logContent = document.getElementById('logContent');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = `[${{timestamp}}] ${{type.toUpperCase()}}: ${{message}}`;
            logContent.innerHTML += logEntry + '\\n';
            logContent.scrollTop = logContent.scrollHeight;
            
            console.log(logEntry);
        }}
        
        function clearLog() {{
            document.getElementById('logContent').innerHTML = '';
        }}
        
        function reloadInterface() {{
            log('Reloading interface...');
            const iframe = document.getElementById('testIframe');
            iframe.src = iframe.src;
        }}
        
        function takeScreenshot() {{
            log('Taking screenshot...');
            // Use html2canvas if available, otherwise just document state
            if (typeof html2canvas !== 'undefined') {{
                html2canvas(document.body).then(canvas => {{
                    const screenshot = canvas.toDataURL('image/png');
                    const img = document.createElement('img');
                    img.src = screenshot;
                    img.className = 'screenshot';
                    document.getElementById('resultsContent').appendChild(img);
                    log('Screenshot captured');
                }});
            }} else {{
                log('Screenshot library not available');
            }}
        }}
        
        function exportResults() {{
            const results = {{
                timestamp: new Date().toISOString(),
                testResults: testResults,
                userAgent: navigator.userAgent,
                url: window.location.href,
                summary: generateSummary()
            }};
            
            const blob = new Blob([JSON.stringify(results, null, 2)], {{
                type: 'application/json'
            }});
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ui_error_detection_${{Date.now()}}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            log('Results exported');
        }}
        
        async function startTests() {{
            log('Starting UI error detection tests...');
            testStartTime = Date.now();
            testResults = [];
            
            const iframe = document.getElementById('testIframe');
            testIframe = iframe;
            
            // Wait for iframe to load
            await waitForIframeLoad();
            
            // Run all tests
            await runErrorBannerTest();
            await runChatButtonTest();
            await runJavaScriptTest();
            await runDOMStructureTest();
            await runNetworkTest();
            
            // Show summary
            showTestSummary();
            
            log('All tests completed');
        }}
        
        function waitForIframeLoad() {{
            return new Promise((resolve) => {{
                const iframe = document.getElementById('testIframe');
                
                function checkLoad() {{
                    try {{
                        if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
                            log('Interface loaded successfully');
                            resolve();
                        }} else {{
                            setTimeout(checkLoad, 100);
                        }}
                    }} catch (e) {{
                        // Cross-origin error - assume loaded
                        log('Interface loaded (cross-origin)');
                        resolve();
                    }}
                }}
                
                checkLoad();
            }});
        }}
        
        async function runErrorBannerTest() {{
            log('Running error banner detection test...');
            
            const testResult = {{
                testName: 'Error Banner Detection',
                status: 'PASS',
                errors: [],
                details: {{}},
                timestamp: new Date().toISOString()
            }};
            
            try {{
                const iframe = document.getElementById('testIframe');
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                
                // Look for error elements
                const errorSelectors = [
                    '.error-banner',
                    '.error-message',
                    '.alert-error',
                    '.notification-error',
                    '.system-error',
                    '.initialization-error',
                    '[data-error]'
                ];
                
                let foundErrors = [];
                
                for (const selector of errorSelectors) {{
                    const elements = iframeDoc.querySelectorAll(selector);
                    for (const element of elements) {{
                        if (element.offsetParent !== null) {{ // is visible
                            foundErrors.push({{
                                selector: selector,
                                text: element.textContent.trim(),
                                html: element.outerHTML.substring(0, 200)
                            }});
                        }}
                    }}
                }}
                
                // Check for error text patterns
                const bodyText = iframeDoc.body.textContent.toLowerCase();
                const errorPatterns = [
                    'initialization error',
                    'error banner',
                    'critical error',
                    'system error',
                    'loading error',
                    'failed to load'
                ];
                
                for (const pattern of errorPatterns) {{
                    if (bodyText.includes(pattern)) {{
                        foundErrors.push({{
                            type: 'text_pattern',
                            pattern: pattern,
                            context: getTextContext(bodyText, pattern)
                        }});
                    }}
                }}
                
                if (foundErrors.length > 0) {{
                    testResult.status = 'FAIL';
                    testResult.errors = foundErrors;
                    testResult.details.errorCount = foundErrors.length;
                    log(`FAIL: Found ${{foundErrors.length}} error banners`, 'error');
                }} else {{
                    log('PASS: No error banners found', 'success');
                }}
                
            }} catch (e) {{
                testResult.status = 'ERROR';
                testResult.errors = [`Test execution failed: ${{e.message}}`];
                log(`ERROR: Error banner test failed: ${{e.message}}`, 'error');
            }}
            
            testResults.push(testResult);
            displayTestResult(testResult);
        }}
        
        async function runChatButtonTest() {{
            log('Running chat button functionality test...');
            
            const testResult = {{
                testName: 'Chat Button Functionality',
                status: 'PASS',
                errors: [],
                details: {{}},
                timestamp: new Date().toISOString()
            }};
            
            try {{
                const iframe = document.getElementById('testIframe');
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                
                // Find chat send button
                const buttonSelectors = [
                    '#chat-send-btn',
                    '.chat-send-btn',
                    '[data-action="send"]',
                    'button[type="submit"]'
                ];
                
                let sendButton = null;
                for (const selector of buttonSelectors) {{
                    const button = iframeDoc.querySelector(selector);
                    if (button && button.offsetParent !== null) {{
                        sendButton = button;
                        break;
                    }}
                }}
                
                if (!sendButton) {{
                    testResult.status = 'FAIL';
                    testResult.errors.push('Chat send button not found');
                    log('FAIL: Chat send button not found', 'error');
                }} else {{
                    // Check button state
                    const buttonState = {{
                        isDisabled: sendButton.disabled,
                        hasDisabledClass: sendButton.classList.contains('disabled'),
                        hasDisabledAttribute: sendButton.hasAttribute('disabled'),
                        cursor: window.getComputedStyle(sendButton).cursor,
                        pointerEvents: window.getComputedStyle(sendButton).pointerEvents
                    }};
                    
                    testResult.details.buttonState = buttonState;
                    
                    // Test input interaction
                    const inputField = iframeDoc.querySelector('#chat-input-field, .chat-input-field');
                    if (inputField) {{
                        // Simulate typing
                        inputField.value = 'test message';
                        inputField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        
                        // Check if button becomes enabled
                        setTimeout(() => {{
                            const isEnabledAfterInput = !sendButton.disabled;
                            testResult.details.enabledAfterInput = isEnabledAfterInput;
                            
                            if (!isEnabledAfterInput && buttonState.isDisabled) {{
                                testResult.status = 'FAIL';
                                testResult.errors.push('Chat send button remains disabled after entering text');
                                log('FAIL: Chat send button remains disabled', 'error');
                            }} else {{
                                log('PASS: Chat send button functionality appears normal', 'success');
                            }}
                            
                            // Clear input
                            inputField.value = '';
                        }}, 500);
                    }} else {{
                        testResult.status = 'FAIL';
                        testResult.errors.push('Chat input field not found');
                        log('FAIL: Chat input field not found', 'error');
                    }}
                }}
                
            }} catch (e) {{
                testResult.status = 'ERROR';
                testResult.errors = [`Test execution failed: ${{e.message}}`];
                log(`ERROR: Chat button test failed: ${{e.message}}`, 'error');
            }}
            
            testResults.push(testResult);
            displayTestResult(testResult);
        }}
        
        async function runJavaScriptTest() {{
            log('Running JavaScript loading test...');
            
            const testResult = {{
                testName: 'JavaScript Loading',
                status: 'PASS',
                errors: [],
                details: {{}},
                timestamp: new Date().toISOString()
            }};
            
            try {{
                const iframe = document.getElementById('testIframe');
                const iframeWin = iframe.contentWindow;
                
                // Check for critical JavaScript objects
                const criticalObjects = [
                    'ChatComponents',
                    'visualizer',
                    'socket',
                    'mermaid'
                ];
                
                let missingObjects = [];
                
                for (const obj of criticalObjects) {{
                    try {{
                        if (typeof iframeWin[obj] === 'undefined') {{
                            missingObjects.push(obj);
                        }}
                    }} catch (e) {{
                        missingObjects.push(obj);
                    }}
                }}
                
                testResult.details.missingObjects = missingObjects;
                
                if (missingObjects.length > 0) {{
                    testResult.status = 'FAIL';
                    testResult.errors.push(`Missing JavaScript objects: ${{missingObjects.join(', ')}}`);
                    log(`FAIL: Missing JavaScript objects: ${{missingObjects.join(', ')}}`, 'error');
                }} else {{
                    log('PASS: Critical JavaScript objects found', 'success');
                }}
                
                // Check for console errors
                // Note: We can't access console errors from iframe due to security restrictions
                testResult.details.consoleAccessible = false;
                
            }} catch (e) {{
                testResult.status = 'ERROR';
                testResult.errors = [`Test execution failed: ${{e.message}}`];
                log(`ERROR: JavaScript test failed: ${{e.message}}`, 'error');
            }}
            
            testResults.push(testResult);
            displayTestResult(testResult);
        }}
        
        async function runDOMStructureTest() {{
            log('Running DOM structure test...');
            
            const testResult = {{
                testName: 'DOM Structure',
                status: 'PASS',
                errors: [],
                details: {{}},
                timestamp: new Date().toISOString()
            }};
            
            try {{
                const iframe = document.getElementById('testIframe');
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                
                // Check for required elements
                const requiredElements = [
                    '#app-title',
                    '#chat-panel',
                    '#chat-send-btn',
                    '#chat-input-field',
                    '#workflow-diagram',
                    '#tdd-diagram',
                    '.status-bar'
                ];
                
                let missingElements = [];
                
                for (const selector of requiredElements) {{
                    const element = iframeDoc.querySelector(selector);
                    if (!element) {{
                        missingElements.push(`${{selector}} (missing)`);
                    }} else if (element.offsetParent === null) {{
                        missingElements.push(`${{selector}} (hidden)`);
                    }}
                }}
                
                testResult.details.missingElements = missingElements;
                
                if (missingElements.length > 0) {{
                    testResult.status = 'FAIL';
                    testResult.errors.push(`Missing DOM elements: ${{missingElements.join(', ')}}`);
                    log(`FAIL: Missing DOM elements: ${{missingElements.join(', ')}}`, 'error');
                }} else {{
                    log('PASS: All required DOM elements found', 'success');
                }}
                
                // Check document title
                const title = iframeDoc.title;
                testResult.details.documentTitle = title;
                
                if (!title || title.includes('error')) {{
                    testResult.status = 'FAIL';
                    testResult.errors.push(`Document title indicates error: ${{title}}`);
                    log(`FAIL: Document title indicates error: ${{title}}`, 'error');
                }}
                
            }} catch (e) {{
                testResult.status = 'ERROR';
                testResult.errors = [`Test execution failed: ${{e.message}}`];
                log(`ERROR: DOM structure test failed: ${{e.message}}`, 'error');
            }}
            
            testResults.push(testResult);
            displayTestResult(testResult);
        }}
        
        async function runNetworkTest() {{
            log('Running network connectivity test...');
            
            const testResult = {{
                testName: 'Network Connectivity',
                status: 'PASS',
                errors: [],
                details: {{}},
                timestamp: new Date().toISOString()
            }};
            
            try {{
                // Test basic connectivity
                const response = await fetch('{self.base_url}/');
                testResult.details.serverResponse = {{
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers)
                }};
                
                if (response.status !== 200) {{
                    testResult.status = 'FAIL';
                    testResult.errors.push(`Server returned status ${{response.status}}`);
                    log(`FAIL: Server returned status ${{response.status}}`, 'error');
                }} else {{
                    log('PASS: Server connectivity normal', 'success');
                }}
                
                // Test API endpoints
                const apiEndpoints = ['/api/status', '/api/interfaces'];
                let apiResults = {{}};
                
                for (const endpoint of apiEndpoints) {{
                    try {{
                        const apiResponse = await fetch('{self.base_url}' + endpoint);
                        apiResults[endpoint] = {{
                            status: apiResponse.status,
                            accessible: apiResponse.status < 400
                        }};
                    }} catch (e) {{
                        apiResults[endpoint] = {{
                            error: e.message,
                            accessible: false
                        }};
                    }}
                }}
                
                testResult.details.apiEndpoints = apiResults;
                
            }} catch (e) {{
                testResult.status = 'ERROR';
                testResult.errors = [`Test execution failed: ${{e.message}}`];
                log(`ERROR: Network test failed: ${{e.message}}`, 'error');
            }}
            
            testResults.push(testResult);
            displayTestResult(testResult);
        }}
        
        function displayTestResult(testResult) {{
            const resultsContent = document.getElementById('resultsContent');
            
            const resultDiv = document.createElement('div');
            resultDiv.className = `test-result ${{testResult.status.toLowerCase()}}`;
            
            let statusIcon = '';
            if (testResult.status === 'PASS') statusIcon = '✅';
            else if (testResult.status === 'FAIL') statusIcon = '❌';
            else if (testResult.status === 'ERROR') statusIcon = '⚠️';
            
            resultDiv.innerHTML = `
                <h4>${{statusIcon}} ${{testResult.testName}} - ${{testResult.status}}</h4>
                <div class="test-details">
                    <p><strong>Timestamp:</strong> ${{testResult.timestamp}}</p>
                    ${{testResult.errors.length > 0 ? `
                        <p><strong>Errors:</strong></p>
                        <ul>${{testResult.errors.map(error => `<li class="error-highlight">${{error}}</li>`).join('')}}</ul>
                    ` : ''}}
                    ${{Object.keys(testResult.details).length > 0 ? `
                        <p><strong>Details:</strong></p>
                        <pre>${{JSON.stringify(testResult.details, null, 2)}}</pre>
                    ` : ''}}
                </div>
            `;
            
            resultsContent.appendChild(resultDiv);
        }}
        
        function showTestSummary() {{
            const testSummary = document.getElementById('testSummary');
            const summaryContent = document.getElementById('summaryContent');
            
            const summary = generateSummary();
            
            summaryContent.innerHTML = `
                <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                    <div><strong>Total Tests:</strong> ${{summary.totalTests}}</div>
                    <div><strong>Passed:</strong> <span style="color: green;">${{summary.passedTests}}</span></div>
                    <div><strong>Failed:</strong> <span style="color: red;">${{summary.failedTests}}</span></div>
                    <div><strong>Errors:</strong> <span style="color: orange;">${{summary.errorTests}}</span></div>
                </div>
                <div><strong>Overall Status:</strong> 
                    <span style="color: ${{summary.overallStatus === 'PASS' ? 'green' : 'red'}}; font-weight: bold;">
                        ${{summary.overallStatus}}
                    </span>
                </div>
                ${{summary.failedTestNames.length > 0 ? `
                    <div style="margin-top: 10px;">
                        <strong>Failed Tests:</strong> ${{summary.failedTestNames.join(', ')}}
                    </div>
                ` : ''}}
            `;
            
            testSummary.style.display = 'block';
        }}
        
        function generateSummary() {{
            const totalTests = testResults.length;
            const passedTests = testResults.filter(r => r.status === 'PASS').length;
            const failedTests = testResults.filter(r => r.status === 'FAIL').length;
            const errorTests = testResults.filter(r => r.status === 'ERROR').length;
            const failedTestNames = testResults.filter(r => r.status === 'FAIL').map(r => r.testName);
            const errorTestNames = testResults.filter(r => r.status === 'ERROR').map(r => r.testName);
            
            return {{
                totalTests,
                passedTests,
                failedTests,
                errorTests,
                failedTestNames,
                errorTestNames,
                overallStatus: failedTests > 0 ? 'FAIL' : (errorTests > 0 ? 'ERROR' : 'PASS')
            }};
        }}
        
        function getTextContext(text, pattern, contextSize = 100) {{
            const index = text.indexOf(pattern);
            if (index === -1) return '';
            
            const start = Math.max(0, index - contextSize);
            const end = Math.min(text.length, index + pattern.length + contextSize);
            
            return text.substring(start, end);
        }}
        
        // Auto-start tests when page loads
        window.addEventListener('load', () => {{
            log('Browser automation test page loaded');
            log('Click "Start Tests" to begin automated error detection');
        }});
    </script>
</body>
</html>
        """
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ui_error_test_{timestamp}.html"
        test_file = Path(__file__).parent / "test_results" / filename
        test_file.parent.mkdir(exist_ok=True)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
            
        self.test_file = test_file
        return str(test_file)
        
    def start_server_if_needed(self) -> bool:
        """Start the web server if not running"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("Web server already running")
                return True
        except:
            pass
            
        try:
            app_path = Path(__file__).parent / "app.py"
            if not app_path.exists():
                print("Error: app.py not found")
                return False
                
            # Start server
            subprocess.Popen(
                [sys.executable, str(app_path), "--port", str(self.port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for server to start
            for i in range(30):
                try:
                    import requests
                    response = requests.get(f"{self.base_url}/", timeout=2)
                    if response.status_code == 200:
                        print(f"Web server started on port {self.port}")
                        return True
                except:
                    time.sleep(1)
                    
            print("Failed to start web server")
            return False
            
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
            
    def run_tests(self) -> str:
        """Generate test file and open in browser"""
        print("Generating browser-based UI test...")
        
        # Start server if needed
        if not self.start_server_if_needed():
            return None
            
        # Generate test HTML
        test_file = self.generate_test_html()
        print(f"Test file generated: {test_file}")
        
        # Open in browser
        try:
            webbrowser.open(f"file://{test_file}")
            print("Test opened in browser")
            print("The test will automatically detect UI errors in the web interface")
            print("Results can be exported from the browser interface")
        except Exception as e:
            print(f"Failed to open browser: {e}")
            print(f"Manually open: file://{test_file}")
            
        return test_file


def main():
    """Main entry point"""
    tester = BrowserAutomationTest()
    
    try:
        test_file = tester.run_tests()
        if test_file:
            print(f"\nTest file created: {test_file}")
            print("The browser-based test will automatically detect:")
            print("- Error banners and initialization errors")
            print("- Chat send button functionality issues")
            print("- JavaScript loading problems")
            print("- DOM structure issues")
            print("- Network connectivity problems")
            print("\nUse the browser interface to run tests and export results.")
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())