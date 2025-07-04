#!/usr/bin/env python3
"""
Lightweight UI Error Checker

A simpler alternative to the full Selenium-based detector that uses
requests and basic HTML parsing to detect UI errors.
"""

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LightweightUIChecker:
    """Lightweight UI checker using requests and HTML parsing"""
    
    def __init__(self, port: int = 5000):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.session = requests.Session() if HAS_REQUESTS else None
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'server_info': {}
        }
        
    def check_server_running(self) -> bool:
        """Check if the web server is running"""
        if not HAS_REQUESTS:
            logger.error("requests library not available")
            return False
            
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            self.results['server_info'] = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_time': response.elapsed.total_seconds()
            }
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Server check failed: {e}")
            return False
            
    def start_server_if_needed(self) -> bool:
        """Start the web server if not already running"""
        if self.check_server_running():
            logger.info("Web server already running")
            return True
            
        try:
            app_path = Path(__file__).parent / "app.py"
            if not app_path.exists():
                logger.error("app.py not found")
                return False
                
            # Start server in background
            subprocess.Popen(
                [sys.executable, str(app_path), "--port", str(self.port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for server to start
            for i in range(30):
                if self.check_server_running():
                    logger.info(f"Web server started on port {self.port}")
                    return True
                time.sleep(1)
                
            logger.error("Failed to start web server")
            return False
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
            
    def check_html_structure(self) -> Dict:
        """Check the HTML structure for errors"""
        test_result = {
            'test_name': 'html_structure',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            response = self.session.get(f"{self.base_url}/")
            html_content = response.text
            
            # Basic HTML validation
            if not html_content.strip():
                test_result['status'] = 'FAIL'
                test_result['errors'].append("Empty HTML response")
                return test_result
                
            # Check for error patterns in HTML
            error_patterns = [
                r'initialization.*error',
                r'error.*banner',
                r'critical.*error',
                r'system.*error',
                r'loading.*error',
                r'failed.*to.*load'
            ]
            
            found_errors = []
            for pattern in error_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    found_errors.extend(matches)
                    
            if found_errors:
                test_result['status'] = 'FAIL'
                test_result['errors'] = found_errors
                test_result['details']['error_patterns'] = found_errors
                
            # Check for required elements
            required_elements = [
                'chat-send-btn',
                'chat-input-field',
                'chat-panel',
                'workflow-diagram',
                'tdd-diagram'
            ]
            
            missing_elements = []
            for element_id in required_elements:
                if element_id not in html_content:
                    missing_elements.append(element_id)
                    
            if missing_elements:
                test_result['status'] = 'FAIL'
                test_result['errors'].append(f"Missing elements: {', '.join(missing_elements)}")
                test_result['details']['missing_elements'] = missing_elements
                
            # Check for JavaScript includes
            js_includes = re.findall(r'<script[^>]*src="([^"]*)"', html_content)
            test_result['details']['javascript_includes'] = js_includes
            
            # Check for CSS includes
            css_includes = re.findall(r'<link[^>]*href="([^"]*\.css)"', html_content)
            test_result['details']['css_includes'] = css_includes
            
            # Check for disabled send button
            if 'chat-send-btn' in html_content:
                # Look for disabled attribute
                send_btn_match = re.search(r'id="chat-send-btn"[^>]*disabled', html_content)
                if send_btn_match:
                    test_result['status'] = 'FAIL'
                    test_result['errors'].append("Chat send button is disabled in HTML")
                    test_result['details']['send_button_disabled'] = True
                else:
                    test_result['details']['send_button_disabled'] = False
                    
            test_result['details']['html_size'] = len(html_content)
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test failed: {str(e)}"]
            
        return test_result
        
    def check_static_resources(self) -> Dict:
        """Check if static resources are loading correctly"""
        test_result = {
            'test_name': 'static_resources',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get main page to find resource URLs
            response = self.session.get(f"{self.base_url}/")
            html_content = response.text
            
            # Extract JavaScript files
            js_files = re.findall(r'<script[^>]*src="([^"]*)"', html_content)
            css_files = re.findall(r'<link[^>]*href="([^"]*\.css)"', html_content)
            
            failed_resources = []
            
            # Check JavaScript files
            for js_file in js_files:
                if js_file.startswith('http'):
                    # External resource
                    try:
                        js_response = self.session.get(js_file, timeout=10)
                        if js_response.status_code != 200:
                            failed_resources.append({
                                'url': js_file,
                                'status': js_response.status_code,
                                'type': 'javascript'
                            })
                    except Exception as e:
                        failed_resources.append({
                            'url': js_file,
                            'error': str(e),
                            'type': 'javascript'
                        })
                else:
                    # Local resource
                    try:
                        local_url = f"{self.base_url}{js_file}"
                        js_response = self.session.get(local_url, timeout=10)
                        if js_response.status_code != 200:
                            failed_resources.append({
                                'url': local_url,
                                'status': js_response.status_code,
                                'type': 'javascript'
                            })
                    except Exception as e:
                        failed_resources.append({
                            'url': local_url,
                            'error': str(e),
                            'type': 'javascript'
                        })
                        
            # Check CSS files
            for css_file in css_files:
                if css_file.startswith('http'):
                    continue  # Skip external CSS for now
                    
                try:
                    local_url = f"{self.base_url}{css_file}"
                    css_response = self.session.get(local_url, timeout=10)
                    if css_response.status_code != 200:
                        failed_resources.append({
                            'url': local_url,
                            'status': css_response.status_code,
                            'type': 'css'
                        })
                except Exception as e:
                    failed_resources.append({
                        'url': local_url,
                        'error': str(e),
                        'type': 'css'
                    })
                    
            test_result['details']['javascript_files'] = js_files
            test_result['details']['css_files'] = css_files
            test_result['details']['failed_resources'] = failed_resources
            
            if failed_resources:
                test_result['status'] = 'FAIL'
                test_result['errors'] = [f"Failed to load {len(failed_resources)} resources"]
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test failed: {str(e)}"]
            
        return test_result
        
    def check_api_endpoints(self) -> Dict:
        """Check if API endpoints are responding"""
        test_result = {
            'test_name': 'api_endpoints',
            'status': 'PASS',
            'errors': [],
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Test common API endpoints
            endpoints = [
                '/api/status',
                '/api/interfaces',
                '/api/projects',
                '/health'
            ]
            
            endpoint_results = {}
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                    endpoint_results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'content_length': len(response.content)
                    }
                    
                    if response.status_code == 200:
                        try:
                            # Try to parse JSON response
                            json_data = response.json()
                            endpoint_results[endpoint]['json_valid'] = True
                            endpoint_results[endpoint]['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else []
                        except:
                            endpoint_results[endpoint]['json_valid'] = False
                            
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'error': str(e),
                        'accessible': False
                    }
                    
            test_result['details']['endpoints'] = endpoint_results
            
            # Check if any critical endpoints are failing
            critical_endpoints = ['/api/status']
            for endpoint in critical_endpoints:
                if endpoint in endpoint_results:
                    result = endpoint_results[endpoint]
                    if 'error' in result or result.get('status_code', 0) >= 400:
                        test_result['status'] = 'FAIL'
                        test_result['errors'].append(f"Critical endpoint {endpoint} failed")
                        
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['errors'] = [f"Test failed: {str(e)}"]
            
        return test_result
        
    def run_all_tests(self) -> Dict:
        """Run all lightweight tests"""
        logger.info("Starting lightweight UI checks...")
        
        # Check if server is running
        if not self.check_server_running():
            if not self.start_server_if_needed():
                self.results['fatal_error'] = "Could not start or connect to web server"
                return self.results
                
        # Wait a moment for server to be ready
        time.sleep(2)
        
        # Run tests
        self.results['tests']['html_structure'] = self.check_html_structure()
        self.results['tests']['static_resources'] = self.check_static_resources()
        self.results['tests']['api_endpoints'] = self.check_api_endpoints()
        
        # Calculate summary
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
        
        return self.results
        
    def print_summary(self):
        """Print test summary"""
        if 'summary' not in self.results:
            print("No test results available")
            return
            
        summary = self.results['summary']
        
        print("\n" + "="*50)
        print("LIGHTWEIGHT UI CHECK SUMMARY")
        print("="*50)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Tests: {summary['passed_tests']}/{summary['total_tests']} passed")
        
        if summary['failed_test_names']:
            print(f"Failed: {', '.join(summary['failed_test_names'])}")
            
        if summary['error_test_names']:
            print(f"Errors: {', '.join(summary['error_test_names'])}")
            
        # Show specific issues
        for test_name, result in self.results['tests'].items():
            if result['status'] in ['FAIL', 'ERROR']:
                print(f"\n{test_name.upper()} ISSUES:")
                for error in result['errors']:
                    print(f"  - {error}")
                    
        print("\n" + "="*50)
        
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lightweight_ui_check_{timestamp}.json"
            
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        results_path = results_dir / filename
        
        try:
            with open(results_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to: {results_path}")
            return str(results_path)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None


def main():
    """Main entry point"""
    if not HAS_REQUESTS:
        print("Error: requests library not installed")
        print("Install with: pip install requests")
        return 1
        
    checker = LightweightUIChecker()
    
    try:
        results = checker.run_all_tests()
        checker.print_summary()
        checker.save_results()
        
        # Return appropriate exit code
        if results.get('summary', {}).get('overall_status') == 'PASS':
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())