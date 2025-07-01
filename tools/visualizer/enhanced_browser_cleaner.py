#!/usr/bin/env python3
"""
Enhanced Browser Cache Cleaner
Generated: 2025-07-01T00:35:23.623738

This script provides comprehensive browser cache clearing specifically
for localhost:5000 with browser-specific optimizations.
"""

import os
import sys
import platform
import subprocess
import shutil
import time
from pathlib import Path

class EnhancedBrowserCleaner:
    def __init__(self):
        self.system = platform.system()
        
    def clear_chrome_comprehensive(self):
        """Comprehensive Chrome cache clearing"""
        print("🔧 Comprehensive Chrome cache clearing...")
        
        # Kill Chrome processes first
        if self.system == "Windows":
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
        else:
            subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
        
        time.sleep(2)
        
        # Clear cache directories
        cache_paths = []
        
        if self.system == "Windows":
            base = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
            cache_paths = [
                base + r"\Default\Cache",
                base + r"\Default\Code Cache", 
                base + r"\Default\Service Worker\CacheStorage",
                base + r"\Default\Session Storage",
                base + r"\Default\Local Storage",
                base + r"\Default\IndexedDB"
            ]
        elif self.system == "Linux":
            home = os.path.expanduser("~")
            cache_paths = [
                home + "/.cache/google-chrome/Default/Cache",
                home + "/.config/google-chrome/Default/Local Storage",
                home + "/.config/google-chrome/Default/Session Storage"
            ]
        elif self.system == "Darwin":
            home = os.path.expanduser("~")
            cache_paths = [
                home + "/Library/Caches/Google/Chrome/Default/Cache",
                home + "/Library/Application Support/Google/Chrome/Default/Local Storage"
            ]
            
        cleared = 0
        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                try:
                    shutil.rmtree(cache_path)
                    print(f"✅ Cleared: {cache_path}")
                    cleared += 1
                except Exception as e:
                    print(f"⚠️ Could not clear {cache_path}: {e}")
                    
        print(f"✅ Cleared {cleared} cache directories")
        return cleared > 0
        
    def launch_chrome_ultra_clean(self):
        """Launch Chrome with ultra-clean cache settings"""
        print("🚀 Launching Chrome with ultra-clean settings...")
        
        chrome_paths = []
        if self.system == "Windows":
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
        elif self.system == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser"
            ]
        elif self.system == "Darwin":
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            ]
            
        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break
                
        if not chrome_exe:
            print("❌ Chrome not found")
            return False
            
        # Ultra-aggressive cache disabling flags
        args = [
            chrome_exe,
            "--incognito",
            "--disable-cache",
            "--disable-application-cache",
            "--disable-offline-load-stale-cache", 
            "--disable-gpu-sandbox",
            "--disable-software-rasterizer",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disk-cache-size=0",
            "--media-cache-size=0",
            "--aggressive-cache-discard",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--disable-translate",
            "--no-first-run",
            "--no-default-browser-check",
            "--memory-pressure-off",
            "--max_old_space_size=4096",
            "--user-data-dir=" + str(Path.home() / "chrome-temp-profile"),
            "http://localhost:5000"
        ]
        
        try:
            subprocess.Popen(args)
            print("✅ Chrome launched with ultra-clean settings")
            return True
        except Exception as e:
            print(f"❌ Failed to launch Chrome: {e}")
            return False
            
    def run_complete_cleanup(self):
        """Run complete cleanup process"""
        print("=" * 50)
        print("🧹 ENHANCED BROWSER CACHE CLEANER")
        print("=" * 50)
        
        success = True
        
        # Step 1: Clear cache
        if not self.clear_chrome_comprehensive():
            success = False
            
        # Step 2: Launch clean browser
        if not self.launch_chrome_ultra_clean():
            success = False
            
        print("\n" + "=" * 50)
        if success:
            print("✅ CLEANUP COMPLETE")
            print("Chrome should now load with completely clean cache")
        else:
            print("⚠️ CLEANUP PARTIALLY SUCCESSFUL")
            print("Try manual cache clearing if issues persist")
            
        return success

if __name__ == "__main__":
    cleaner = EnhancedBrowserCleaner()
    cleaner.run_complete_cleanup()
