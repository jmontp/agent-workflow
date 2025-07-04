#!/usr/bin/env python3
"""
Integration Validation Test Script

Tests the complete integration from orchestrator → state broadcaster → web interface
and validates that the three UI issues are resolved.
"""

import asyncio
import json
import time
import requests
import websockets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class IntegrationValidator:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.ws_url = "ws://localhost:8080"
        self.driver = None
        self.results = {
            "state_broadcaster_connection": False,
            "web_interface_accessible": False,
            "initialization_error_resolved": False,
            "chat_send_button_working": False,
            "layout_button_fixed": False,
            "websocket_connection_working": False,
            "end_to_end_integration": False
        }
    
    def setup_driver(self):
        """Setup Chrome driver for testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless Chrome
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return False
    
    async def test_state_broadcaster_connection(self):
        """Test that state broadcaster WebSocket is accessible"""
        print("🔍 Testing state broadcaster connection...")
        try:
            async with websockets.connect(self.ws_url, timeout=5) as websocket:
                # Send a test message
                await websocket.send(json.dumps({"type": "ping"}))
                print("✅ State broadcaster WebSocket is accessible")
                self.results["state_broadcaster_connection"] = True
                return True
        except Exception as e:
            print(f"❌ State broadcaster connection failed: {e}")
            return False
    
    def test_web_interface_accessible(self):
        """Test that web interface is accessible"""
        print("🔍 Testing web interface accessibility...")
        try:
            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print("✅ Web interface is accessible")
                self.results["web_interface_accessible"] = True
                return True
            else:
                print(f"❌ Web interface returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Web interface not accessible: {e}")
            return False
    
    def test_initialization_error_banner(self):
        """Test that initialization error banner is resolved"""
        print("🔍 Testing initialization error banner...")
        try:
            self.driver.get(self.base_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for error banners or initialization errors
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .banner")
            initialization_errors = [el for el in error_elements if "initialization" in el.text.lower()]
            
            if not initialization_errors:
                print("✅ No initialization error banners found")
                self.results["initialization_error_resolved"] = True
                return True
            else:
                print(f"❌ Found initialization errors: {[el.text for el in initialization_errors]}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing initialization banner: {e}")
            return False
    
    def test_chat_send_button(self):
        """Test that chat send button is working"""
        print("🔍 Testing chat send button functionality...")
        try:
            # Wait for chat elements to load
            chat_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "chat-input-field"))
            )
            send_button = self.driver.find_element(By.ID, "chat-send-btn")
            
            # Test that button starts disabled
            if send_button.get_attribute("disabled"):
                print("✅ Send button correctly starts disabled")
            
            # Type a message
            chat_input.send_keys("test message")
            
            # Button should now be enabled
            if not send_button.get_attribute("disabled"):
                print("✅ Send button enables when text is entered")
                
                # Check if button is clickable (not showing cross cursor)
                cursor_style = send_button.value_of_css_property("cursor")
                if cursor_style != "not-allowed":
                    print("✅ Send button is clickable (correct cursor)")
                    self.results["chat_send_button_working"] = True
                    return True
                else:
                    print("❌ Send button still shows not-allowed cursor")
                    return False
            else:
                print("❌ Send button remains disabled even with text")
                return False
                
        except Exception as e:
            print(f"❌ Error testing chat send button: {e}")
            return False
    
    def test_layout_button(self):
        """Test that layout button is fixed or properly hidden"""
        print("🔍 Testing layout button fix...")
        try:
            layout_button = self.driver.find_element(By.ID, "emergency-reset-btn")
            
            # Check if button is hidden or has working onclick
            is_hidden = layout_button.value_of_css_property("display") == "none"
            onclick_attr = layout_button.get_attribute("onclick")
            
            if is_hidden:
                print("✅ Layout button is properly hidden")
                self.results["layout_button_fixed"] = True
                return True
            elif onclick_attr and "forceVisualizerLayout" in onclick_attr:
                print("✅ Layout button has correct function call")
                self.results["layout_button_fixed"] = True
                return True
            else:
                print(f"❌ Layout button issue: hidden={is_hidden}, onclick={onclick_attr}")
                return False
                
        except NoSuchElementException:
            print("✅ Layout button removed completely")
            self.results["layout_button_fixed"] = True
            return True
        except Exception as e:
            print(f"❌ Error testing layout button: {e}")
            return False
    
    def test_websocket_connection(self):
        """Test that frontend WebSocket connection is working"""
        print("🔍 Testing frontend WebSocket connection...")
        try:
            # Wait for connection status to update
            connection_status = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "connection-status"))
            )
            
            # Wait a bit for connection to establish
            time.sleep(3)
            
            status_text = connection_status.text.lower()
            if "connected" in status_text:
                print("✅ Frontend shows connected status")
                self.results["websocket_connection_working"] = True
                return True
            else:
                print(f"❌ Frontend shows status: {status_text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing WebSocket connection: {e}")
            return False
    
    def test_end_to_end_integration(self):
        """Test complete end-to-end integration"""
        print("🔍 Testing end-to-end integration...")
        try:
            # Check if all core components are working together
            core_working = all([
                self.results["state_broadcaster_connection"],
                self.results["web_interface_accessible"],
                self.results["websocket_connection_working"]
            ])
            
            ui_issues_fixed = all([
                self.results["initialization_error_resolved"],
                self.results["chat_send_button_working"],
                self.results["layout_button_fixed"]
            ])
            
            if core_working and ui_issues_fixed:
                print("✅ Complete end-to-end integration working")
                self.results["end_to_end_integration"] = True
                return True
            else:
                print(f"❌ Integration incomplete - Core: {core_working}, UI: {ui_issues_fixed}")
                return False
                
        except Exception as e:
            print(f"❌ Error in end-to-end test: {e}")
            return False
    
    async def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting Integration Validation...")
        print("=" * 60)
        
        # Test backend connectivity
        await self.test_state_broadcaster_connection()
        self.test_web_interface_accessible()
        
        # Setup browser for frontend tests
        if not self.setup_driver():
            print("❌ Cannot run frontend tests without browser driver")
            return self.results
        
        try:
            # Test UI issues
            self.test_initialization_error_banner()
            self.test_chat_send_button()
            self.test_layout_button()
            self.test_websocket_connection()
            
            # Final integration test
            self.test_end_to_end_integration()
            
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.results
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("🔍 VALIDATION RESULTS")
        print("=" * 60)
        
        for test_name, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        total_tests = len(self.results)
        passed_tests = sum(self.results.values())
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL ISSUES RESOLVED! Integration validation successful.")
            return True
        else:
            print("⚠️  Some issues remain. See failed tests above.")
            return False

async def main():
    """Main validation runner"""
    validator = IntegrationValidator()
    
    print("Waiting 5 seconds for services to stabilize...")
    await asyncio.sleep(5)
    
    results = await validator.run_validation()
    success = validator.print_results()
    
    # Save results to file
    with open("/tmp/integration_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: /tmp/integration_validation_results.json")
    return success

if __name__ == "__main__":
    asyncio.run(main())