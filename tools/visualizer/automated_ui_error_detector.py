#!/usr/bin/env python3
"""
Automated UI Error Detection System

This script automatically detects specific UI errors in the web visualizer:
1. Page reload initialization error banners
2. Chat send button non-clickable state
3. Missing JavaScript file loading issues
4. DOM state validation

Usage:
    python automated_ui_error_detector.py [--continuous] [--port 5000] [--debug]
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Third-party imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, WebDriverException
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ui_error_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UIErrorDetector:
    """Main class for automated UI error detection"""
    
    def __init__(self, port: int = 5000, debug: bool = False):
        self.port = port
        self.debug = debug
        self.base_url = f"http://localhost:{port}"
        self.driver = None
        self.web_server_process = None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'screenshots': [],
            'network_errors': [],
            'console_logs': []
        }
        
        # Error detection patterns
        self.error_patterns = {
            'initialization_error': [
                'initialization error',
                'error banner',
                'failed to load',
                'initialization failed',
                'critical error',
                'system error',
                'loading error'
            ],
            'chat_errors': [
                'chat error',
                'send button disabled',
                'chat not responding',
                'websocket error',
                'connection failed'
            ],
            'javascript_errors': [
                'script error',
                'uncaught error',
                'reference error',
                'type error',
                'syntax error',
                'network error'
            ]
        }
        
    def setup_driver(self) -> bool:
        """Set up Chrome WebDriver with appropriate options"""
        if not HAS_SELENIUM:
            logger.error("Selenium not installed. Install with: pip install selenium")
            return False
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Enable logging
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--log-level=0")
            
            if self.debug:
                chrome_options.add_argument("--remote-debugging-port=9222")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Enable network monitoring
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            logger.info("Chrome WebDriver setup complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False
            
    def start_web_server(self) -> bool:
        """Start the Flask web server if not already running"""
        try:
            # Check if server is already running
            import requests
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                logger.info("Web server already running")
                return True
        except:
            pass
            
        try:
            # Start the web server
            app_path = Path(__file__).parent / "app.py"
            if not app_path.exists():
                logger.error("app.py not found")
                return False
                
            env = os.environ.copy()
            env['FLASK_ENV'] = 'development'
            env['FLASK_DEBUG'] = '1' if self.debug else '0'
            
            self.web_server_process = subprocess.Popen(
                [sys.executable, str(app_path), "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # Wait for server to start
            max_retries = 30
            for i in range(max_retries):
                try:
                    import requests
                    response = requests.get(f"{self.base_url}/", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"Web server started on port {self.port}")
                        return True
                except:
                    time.sleep(1)
                    
            logger.error("Web server failed to start")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
            return False
            
    def capture_screenshot(self, filename: str) -> str:
        """Capture a screenshot and return the path"""
        if not self.driver:
            return None
            
        try:
            screenshot_dir = Path(__file__).parent / "screenshots"
            screenshot_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = screenshot_dir / f"{timestamp}_{filename}.png"
            
            self.driver.save_screenshot(str(screenshot_path))
            self.results['screenshots'].append(str(screenshot_path))
            
            logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
            
    def get_console_logs(self) -> List[Dict]:
        """Get browser console logs"""
        if not self.driver:
            return []
            
        try:
            logs = self.driver.get_log('browser')
            console_logs = []
            
            for log in logs:
                console_logs.append({
                    'timestamp': log['timestamp'],
                    'level': log['level'],
                    'message': log['message'],
                    'source': log.get('source', 'unknown')
                })
                
            return console_logs
            
        except Exception as e:
            logger.error(f"Failed to get console logs: {e}")
            return []
            
    def detect_error_banners(self) -> Dict:
        """Detect initialization error banners in the UI"""
        logger.info("Detecting error banners...")
        
        test_result = {
            'test_name': 'error_banner_detection',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for error banners and messages
            error_selectors = [
                '.error-banner',
                '.error-message',
                '.alert-error',
                '.notification-error',
                '.system-error',
                '.initialization-error',
                '[data-error]',
                '.error'
            ]
            
            found_errors = []
            
            for selector in error_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            error_text = element.text.strip()
                            if error_text:
                                found_errors.append({
                                    'selector': selector,
                                    'text': error_text,
                                    'html': element.get_attribute('outerHTML')[:500]
                                })
                except:
                    continue
                    
            # Check for error text in page content
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for pattern in self.error_patterns['initialization_error']:
                if pattern in page_text:
                    found_errors.append({
                        'type': 'text_pattern',
                        'pattern': pattern,
                        'context': self.get_context_around_text(page_text, pattern)
                    })
                    
            if found_errors:
                test_result['status'] = 'FAIL'
                test_result['errors'] = found_errors
                test_result['details']['error_count'] = len(found_errors)
                
                # Capture screenshot of error state
                screenshot_path = self.capture_screenshot("error_banners")
                test_result['details']['screenshot'] = screenshot_path
                
                logger.warning(f"Found {len(found_errors)} error banners/messages")
            else:
                logger.info("No error banners detected")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test execution failed: {str(e)}"]
            logger.error(f"Error banner detection failed: {e}")
            
        return test_result
        
    def detect_chat_button_issues(self) -> Dict:
        """Detect chat send button functionality issues"""
        logger.info("Detecting chat button issues...")
        
        test_result = {
            'test_name': 'chat_button_functionality',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Find chat send button
            chat_send_selectors = [
                '#chat-send-btn',
                '.chat-send-btn',
                '[data-action="send"]',
                'button[type="submit"]'
            ]
            
            send_button = None
            for selector in chat_send_selectors:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if send_button.is_displayed():
                        break
                except:
                    continue
                    
            if not send_button:
                test_result['status'] = 'FAIL'
                test_result['errors'].append("Chat send button not found")
                return test_result
                
            # Check if button is disabled
            is_disabled = send_button.get_attribute('disabled')
            has_disabled_class = 'disabled' in send_button.get_attribute('class')
            
            button_details = {
                'element_found': True,
                'is_displayed': send_button.is_displayed(),
                'is_enabled': send_button.is_enabled(),
                'disabled_attribute': is_disabled,
                'disabled_class': has_disabled_class,
                'css_cursor': send_button.value_of_css_property('cursor'),
                'css_pointer_events': send_button.value_of_css_property('pointer-events'),
                'outer_html': send_button.get_attribute('outerHTML')
            }
            
            test_result['details']['button_state'] = button_details
            
            # Try to click the button
            try:
                # First try to focus on input field
                input_field = self.driver.find_element(By.CSS_SELECTOR, '#chat-input-field, .chat-input-field')
                if input_field:
                    input_field.click()
                    input_field.send_keys("test message")
                    
                    # Wait a moment for any dynamic updates
                    time.sleep(0.5)
                    
                    # Check if button is now enabled
                    is_enabled_after_input = send_button.is_enabled()
                    test_result['details']['enabled_after_input'] = is_enabled_after_input
                    
                    if not is_enabled_after_input:
                        test_result['status'] = 'FAIL'
                        test_result['errors'].append("Chat send button remains disabled after entering text")
                        
                # Try to click the button
                actions = ActionChains(self.driver)
                actions.move_to_element(send_button).click().perform()
                
                # Check for any click events or responses
                time.sleep(1)
                
                # Clear input field
                if input_field:
                    input_field.clear()
                    
            except Exception as e:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Failed to interact with chat button: {str(e)}")
                
            # Capture screenshot of chat state
            screenshot_path = self.capture_screenshot("chat_button_state")
            test_result['details']['screenshot'] = screenshot_path
            
            if test_result['status'] == 'FAIL':
                logger.warning(f"Chat button issues detected: {test_result['errors']}")
            else:
                logger.info("Chat button functionality appears normal")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test execution failed: {str(e)}"]
            logger.error(f"Chat button detection failed: {e}")
            
        return test_result
        
    def detect_javascript_loading_issues(self) -> Dict:
        """Detect JavaScript file loading issues"""
        logger.info("Detecting JavaScript loading issues...")
        
        test_result = {
            'test_name': 'javascript_loading',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get network logs
            network_logs = self.driver.get_log('performance')
            
            failed_requests = []
            js_requests = []
            
            for log in network_logs:
                message = json.loads(log['message'])
                
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response['url']
                    status = response['status']
                    
                    # Check for JavaScript files
                    if url.endswith('.js') or 'javascript' in response.get('mimeType', ''):
                        js_requests.append({
                            'url': url,
                            'status': status,
                            'mime_type': response.get('mimeType', ''),
                            'timestamp': log['timestamp']
                        })
                        
                        # Check for failed requests
                        if status >= 400:
                            failed_requests.append({
                                'url': url,
                                'status': status,
                                'status_text': response.get('statusText', ''),
                                'timestamp': log['timestamp']
                            })
                            
            # Check console logs for JavaScript errors
            console_logs = self.get_console_logs()
            js_errors = []
            
            for log in console_logs:
                if log['level'] == 'SEVERE':
                    # Check if it's a JavaScript error
                    message = log['message'].lower()
                    if any(pattern in message for pattern in self.error_patterns['javascript_errors']):
                        js_errors.append(log)
                        
            test_result['details']['javascript_requests'] = js_requests
            test_result['details']['failed_requests'] = failed_requests
            test_result['details']['javascript_errors'] = js_errors
            
            if failed_requests:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Found {len(failed_requests)} failed JavaScript requests")
                
            if js_errors:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Found {len(js_errors)} JavaScript console errors")
                
            # Check for specific missing functions or components
            missing_components = []
            
            # Check for critical global objects
            critical_objects = [
                'ChatComponents',
                'visualizer',
                'socket',
                'mermaid'
            ]
            
            for obj in critical_objects:
                try:
                    result = self.driver.execute_script(f"return typeof {obj}")
                    if result == 'undefined':
                        missing_components.append(obj)
                except:
                    missing_components.append(obj)
                    
            if missing_components:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Missing JavaScript components: {', '.join(missing_components)}")
                test_result['details']['missing_components'] = missing_components
                
            # Capture screenshot if there are issues
            if test_result['status'] == 'FAIL':
                screenshot_path = self.capture_screenshot("javascript_issues")
                test_result['details']['screenshot'] = screenshot_path
                logger.warning(f"JavaScript loading issues detected: {test_result['errors']}")
            else:
                logger.info("No JavaScript loading issues detected")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test execution failed: {str(e)}"]
            logger.error(f"JavaScript loading detection failed: {e}")
            
        return test_result
        
    def detect_dom_state_issues(self) -> Dict:
        """Detect DOM state and structural issues"""
        logger.info("Detecting DOM state issues...")
        
        test_result = {
            'test_name': 'dom_state_validation',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check for required DOM elements
            required_elements = [
                '#app-title',
                '#chat-panel',
                '#chat-send-btn',
                '#chat-input-field',
                '#workflow-diagram',
                '#tdd-diagram',
                '.status-bar'
            ]
            
            missing_elements = []
            for selector in required_elements:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if not element.is_displayed():
                        missing_elements.append(f"{selector} (hidden)")
                except:
                    missing_elements.append(f"{selector} (missing)")
                    
            if missing_elements:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Missing required DOM elements: {', '.join(missing_elements)}")
                test_result['details']['missing_elements'] = missing_elements
                
            # Check for layout issues
            layout_issues = []
            
            # Check body dimensions
            body_size = self.driver.get_window_size()
            test_result['details']['window_size'] = body_size
            
            # Check for overflow issues
            try:
                overflow_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    '[style*="overflow"], .overflow-hidden, .overflow-auto'
                )
                test_result['details']['overflow_elements'] = len(overflow_elements)
            except:
                pass
                
            # Check for z-index issues
            try:
                high_z_elements = self.driver.execute_script("""
                    const elements = document.querySelectorAll('*');
                    const highZ = [];
                    elements.forEach(el => {
                        const z = window.getComputedStyle(el).zIndex;
                        if (z && z !== 'auto' && parseInt(z) > 1000) {
                            highZ.push({tag: el.tagName, id: el.id, class: el.className, zIndex: z});
                        }
                    });
                    return highZ;
                """)
                test_result['details']['high_z_index_elements'] = high_z_elements
            except:
                pass
                
            # Capture screenshot for DOM state
            screenshot_path = self.capture_screenshot("dom_state")
            test_result['details']['screenshot'] = screenshot_path
            
            if test_result['status'] == 'FAIL':
                logger.warning(f"DOM state issues detected: {test_result['errors']}")
            else:
                logger.info("DOM state appears normal")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test execution failed: {str(e)}"]
            logger.error(f"DOM state detection failed: {e}")
            
        return test_result
        
    def get_context_around_text(self, text: str, pattern: str, context_size: int = 100) -> str:
        """Get context around found text pattern"""
        index = text.find(pattern)
        if index == -1:
            return ""
            
        start = max(0, index - context_size)
        end = min(len(text), index + len(pattern) + context_size)
        
        return text[start:end]
        
    def run_all_tests(self) -> Dict:
        """Run all UI error detection tests"""
        logger.info("Starting comprehensive UI error detection...")
        
        try:
            # Navigate to the web interface
            self.driver.get(self.base_url)
            
            # Wait for initial page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Run all detection tests
            self.results['tests']['error_banners'] = self.detect_error_banners()
            self.results['tests']['chat_button'] = self.detect_chat_button_issues()
            self.results['tests']['javascript_loading'] = self.detect_javascript_loading_issues()
            self.results['tests']['dom_state'] = self.detect_dom_state_issues()
            
            # Get final console logs
            self.results['console_logs'] = self.get_console_logs()
            
            # Calculate overall status
            failed_tests = [name for name, result in self.results['tests'].items() if result['status'] == 'FAIL']
            error_tests = [name for name, result in self.results['tests'].items() if result['status'] == 'ERROR']
            
            self.results['summary'] = {
                'total_tests': len(self.results['tests']),
                'passed_tests': len(self.results['tests']) - len(failed_tests) - len(error_tests),
                'failed_tests': len(failed_tests),
                'error_tests': len(error_tests),
                'failed_test_names': failed_tests,
                'error_test_names': error_tests,
                'overall_status': 'FAIL' if failed_tests else ('ERROR' if error_tests else 'PASS')
            }
            
            logger.info(f"UI error detection complete. Overall status: {self.results['summary']['overall_status']}")
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            self.results['execution_error'] = str(e)
            
        return self.results
        
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save test results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ui_error_detection_results_{timestamp}.json"
            
        results_path = Path(__file__).parent / "results" / filename
        results_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
                
            logger.info(f"Results saved to: {results_path}")
            return str(results_path)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None
            
    def print_summary(self):
        """Print a summary of test results"""
        if 'summary' not in self.results:
            print("No test results available")
            return
            
        summary = self.results['summary']
        
        print("\n" + "="*60)
        print("UI ERROR DETECTION SUMMARY")
        print("="*60)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Errors: {summary['error_tests']}")
        
        if summary['failed_test_names']:
            print(f"\nFailed Tests: {', '.join(summary['failed_test_names'])}")
            
        if summary['error_test_names']:
            print(f"Error Tests: {', '.join(summary['error_test_names'])}")
            
        print(f"\nTimestamp: {self.results['timestamp']}")
        
        # Print detailed results for failed tests
        for test_name, result in self.results['tests'].items():
            if result['status'] in ['FAIL', 'ERROR']:
                print(f"\n--- {test_name.upper()} DETAILS ---")
                print(f"Status: {result['status']}")
                if result['errors']:
                    print("Errors:")
                    for error in result['errors']:
                        print(f"  - {error}")
                        
        print("\n" + "="*60)
        
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            
        if self.web_server_process:
            self.web_server_process.terminate()
            self.web_server_process.wait()
            
        logger.info("Cleanup complete")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Automated UI Error Detection System')
    parser.add_argument('--continuous', action='store_true', 
                       help='Run continuously with periodic checks')
    parser.add_argument('--port', type=int, default=5000, 
                       help='Port for web server (default: 5000)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('--interval', type=int, default=300, 
                       help='Check interval in seconds for continuous mode (default: 300)')
    
    args = parser.parse_args()
    
    if not HAS_SELENIUM:
        print("Error: Selenium is not installed")
        print("Install with: pip install selenium")
        print("Also ensure ChromeDriver is installed and in PATH")
        return 1
        
    detector = UIErrorDetector(port=args.port, debug=args.debug)
    
    try:
        # Setup
        if not detector.setup_driver():
            return 1
            
        if not detector.start_web_server():
            return 1
            
        if args.continuous:
            logger.info(f"Starting continuous monitoring (interval: {args.interval}s)")
            
            while True:
                try:
                    results = detector.run_all_tests()
                    detector.print_summary()
                    
                    # Save results
                    results_file = detector.save_results()
                    
                    # Wait for next check
                    time.sleep(args.interval)
                    
                except KeyboardInterrupt:
                    logger.info("Stopping continuous monitoring")
                    break
                except Exception as e:
                    logger.error(f"Error in continuous monitoring: {e}")
                    time.sleep(60)  # Wait before retrying
                    
        else:
            # Single run
            results = detector.run_all_tests()
            detector.print_summary()
            
            # Save results
            results_file = detector.save_results()
            
            # Return appropriate exit code
            if results.get('summary', {}).get('overall_status') == 'PASS':
                return 0
            else:
                return 1
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
        
    finally:
        detector.cleanup()


if __name__ == "__main__":
    sys.exit(main())