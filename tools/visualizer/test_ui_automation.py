#!/usr/bin/env python3
"""Automated UI test to verify chat functionality"""

import asyncio
import json
from playwright.async_api import async_playwright
import sys

async def test_chat_interface():
    """Test the chat interface functionality using Playwright"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Collect console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        
        # Navigate to the app
        print("📝 Navigating to http://localhost:5000...")
        await page.goto("http://localhost:5000")
        await page.wait_for_timeout(2000)  # Wait for page to fully load
        
        # Check if chat elements exist
        print("\n🔍 Checking for chat elements...")
        chat_input = await page.query_selector("#chat-input-field")
        send_button = await page.query_selector("#chat-send-btn")
        
        if not chat_input or not send_button:
            print("❌ Chat elements not found!")
            await browser.close()
            return False
            
        print("✅ Chat elements found")
        
        # Check initial button state
        print("\n🔍 Checking initial button state...")
        is_disabled = await send_button.is_disabled()
        print(f"Initial button disabled state: {is_disabled}")
        
        # Type in the input field
        print("\n📝 Typing in chat input...")
        await chat_input.fill("Test message")
        await page.wait_for_timeout(500)  # Wait for event handlers
        
        # Check button state after typing
        is_disabled_after = await send_button.is_disabled()
        print(f"Button disabled after typing: {is_disabled_after}")
        
        # Get input value
        input_value = await chat_input.evaluate("el => el.value")
        print(f"Input field value: '{input_value}'")
        
        # Try clicking the button
        if not is_disabled_after:
            print("\n🖱️ Clicking send button...")
            await send_button.click()
            await page.wait_for_timeout(500)
            
            # Check if input was cleared
            input_value_after = await chat_input.evaluate("el => el.value")
            print(f"Input field after click: '{input_value_after}'")
            
            # Check button state after click
            is_disabled_final = await send_button.is_disabled()
            print(f"Button disabled after click: {is_disabled_final}")
        
        # Print console logs
        print("\n📋 Console logs:")
        for log in console_logs:
            print(f"  {log}")
        
        # Take a screenshot for debugging
        await page.screenshot(path="chat_test_screenshot.png")
        print("\n📸 Screenshot saved as chat_test_screenshot.png")
        
        await browser.close()
        
        # Determine success
        success = not is_disabled_after  # Button should be enabled after typing
        return success

async def test_with_selenium():
    """Fallback test using Selenium if Playwright not available"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    import time
    
    print("Using Selenium for testing...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the app
        print("📝 Navigating to http://localhost:5000...")
        driver.get("http://localhost:5000")
        time.sleep(2)
        
        # Find elements
        print("\n🔍 Checking for chat elements...")
        chat_input = driver.find_element(By.ID, "chat-input-field")
        send_button = driver.find_element(By.ID, "chat-send-btn")
        
        # Check initial state
        print("\n🔍 Checking initial button state...")
        is_disabled = send_button.get_attribute("disabled")
        print(f"Initial button disabled: {is_disabled}")
        
        # Type in input
        print("\n📝 Typing in chat input...")
        chat_input.send_keys("Test message")
        time.sleep(0.5)
        
        # Check button state after typing
        is_disabled_after = send_button.get_attribute("disabled")
        print(f"Button disabled after typing: {is_disabled_after}")
        
        # Get console logs
        logs = driver.get_log('browser')
        print("\n📋 Browser console logs:")
        for log in logs:
            print(f"  {log['level']}: {log['message']}")
        
        driver.save_screenshot("selenium_screenshot.png")
        print("\n📸 Screenshot saved as selenium_screenshot.png")
        
        return is_disabled_after is None or is_disabled_after == "false"
        
    finally:
        driver.quit()

async def simple_http_test():
    """Simple HTTP test to verify the server is serving correct files"""
    import aiohttp
    
    print("🌐 Running HTTP tests...")
    
    async with aiohttp.ClientSession() as session:
        # Test if server is running
        try:
            async with session.get('http://localhost:5000') as resp:
                print(f"✅ Server responding: {resp.status}")
        except Exception as e:
            print(f"❌ Server not responding: {e}")
            return False
        
        # Check if JS file has our changes
        async with session.get('http://localhost:5000/static/js/discord-chat.js') as resp:
            js_content = await resp.text()
            
            # Look for our specific changes
            checks = [
                ("Initial state comment", "// Initial state - disable send button if input is empty"),
                ("Initial state code", "sendButton.disabled = messageInput.value.trim().length === 0;"),
                ("Console log", "console.log('Input changed, has content:'"),
                ("Send button click log", "console.log('Send button clicked');")
            ]
            
            print("\n🔍 Checking JavaScript file for our changes:")
            all_found = True
            for name, text in checks:
                if text in js_content:
                    print(f"  ✅ Found: {name}")
                else:
                    print(f"  ❌ Missing: {name}")
                    all_found = False
            
            return all_found

async def main():
    """Run all tests"""
    print("🚀 Starting automated UI tests...\n")
    
    # First run HTTP test
    http_result = await simple_http_test()
    if not http_result:
        print("\n❌ HTTP test failed - server may not be serving correct files")
        return
    
    # Try Playwright first
    try:
        import playwright
        print("\n🎭 Using Playwright for browser automation...")
        success = await test_chat_interface()
        if success:
            print("\n✅ Chat interface test PASSED!")
        else:
            print("\n❌ Chat interface test FAILED!")
    except ImportError:
        print("\n⚠️  Playwright not installed, trying Selenium...")
        try:
            success = await test_with_selenium()
            if success:
                print("\n✅ Chat interface test PASSED!")
            else:
                print("\n❌ Chat interface test FAILED!")
        except Exception as e:
            print(f"\n❌ Selenium test failed: {e}")
            print("\n💡 Install either playwright or selenium for browser testing:")
            print("   pip install playwright && playwright install chromium")
            print("   OR")
            print("   pip install selenium")

if __name__ == "__main__":
    asyncio.run(main())