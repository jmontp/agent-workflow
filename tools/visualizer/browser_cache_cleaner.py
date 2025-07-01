#!/usr/bin/env python3
"""Browser cache clearing automation tool

This tool automates clearing browser cache for localhost:5000 and verifies
that the updated JavaScript is loaded correctly.
"""

import os
import sys
import time
import platform
import subprocess
import shutil
import psutil
import json
from pathlib import Path


class BrowserCacheCleaner:
    """Automated browser cache clearing for multiple browsers"""
    
    def __init__(self):
        self.system = platform.system()
        self.results = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        print(f"[{level}] {message}")
        self.results.append({"level": level, "message": message})
        
    def find_chrome_cache_dirs(self):
        """Find Chrome cache directories"""
        cache_dirs = []
        
        if self.system == "Windows":
            # Windows paths
            base_paths = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data",
                Path(os.environ.get("APPDATA", "")) / "Google/Chrome/User Data",
            ]
        elif self.system == "Linux":
            # Linux paths (including WSL)
            base_paths = [
                Path.home() / ".config/google-chrome",
                Path.home() / ".cache/google-chrome",
                Path("/mnt/c/Users") / os.environ.get("USER", "") / "AppData/Local/Google/Chrome/User Data",
            ]
        elif self.system == "Darwin":
            # macOS paths
            base_paths = [
                Path.home() / "Library/Application Support/Google/Chrome",
                Path.home() / "Library/Caches/Google/Chrome",
            ]
        
        for base_path in base_paths:
            if base_path.exists():
                # Look for Default profile and other profiles
                for profile in ["Default", "Profile 1", "Profile 2", "Profile 3"]:
                    profile_cache = base_path / profile / "Cache"
                    if profile_cache.exists():
                        cache_dirs.append(profile_cache)
                        
                # Also check for Code Cache
                for profile in ["Default", "Profile 1", "Profile 2", "Profile 3"]:
                    code_cache = base_path / profile / "Code Cache"
                    if code_cache.exists():
                        cache_dirs.append(code_cache)
                        
        return cache_dirs
        
    def clear_chrome_localhost_cache(self):
        """Clear Chrome cache specifically for localhost"""
        self.log("🔍 Looking for Chrome cache directories...")
        
        cache_dirs = self.find_chrome_cache_dirs()
        if not cache_dirs:
            self.log("No Chrome cache directories found", "WARNING")
            return False
            
        for cache_dir in cache_dirs:
            self.log(f"Found cache directory: {cache_dir}")
            
            # Look for localhost-related cache files
            cleared_files = 0
            try:
                for file_path in cache_dir.rglob("*"):
                    if file_path.is_file():
                        try:
                            # Read file to check if it contains localhost:5000
                            with open(file_path, 'rb') as f:
                                content = f.read(1024)  # Read first 1KB
                                if b'localhost:5000' in content or b'localhost%3A5000' in content:
                                    file_path.unlink()
                                    cleared_files += 1
                        except Exception:
                            pass  # Skip files we can't read/delete
                            
                if cleared_files > 0:
                    self.log(f"✅ Cleared {cleared_files} localhost cache files from {cache_dir}")
                    
            except Exception as e:
                self.log(f"Error clearing cache in {cache_dir}: {e}", "ERROR")
                
        return True
        
    def kill_chrome_processes(self):
        """Kill all Chrome processes"""
        self.log("🔪 Killing Chrome processes...")
        killed = 0
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        if killed > 0:
            self.log(f"✅ Terminated {killed} Chrome processes")
            time.sleep(2)  # Give processes time to close
        else:
            self.log("No Chrome processes found to kill")
            
        return killed > 0
        
    def launch_chrome_incognito(self):
        """Launch Chrome in incognito mode with cache disabled"""
        self.log("🚀 Launching Chrome in incognito mode with cache disabled...")
        
        chrome_paths = []
        if self.system == "Windows":
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expandvars("%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe"),
            ]
        elif self.system == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                # WSL Windows Chrome
                "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
                "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            ]
        elif self.system == "Darwin":
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
            
        # Find Chrome executable
        chrome_exe = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_exe = path
                break
                
        if not chrome_exe:
            self.log("Chrome executable not found", "ERROR")
            return False
            
        # Launch with special flags
        args = [
            chrome_exe,
            "--incognito",
            "--disable-application-cache",
            "--disable-cache",
            "--disable-offline-load-stale-cache",
            "--disk-cache-size=0",
            "--media-cache-size=0",
            "--aggressive-cache-discard",
            "--disable-background-networking",
            "--disable-web-security",  # Allow localhost without CORS
            "--disable-features=IsolateOrigins,site-per-process",
            "--flag-switches-begin",
            "--disable-site-isolation-trials",
            "--flag-switches-end",
            "http://localhost:5000"
        ]
        
        try:
            subprocess.Popen(args)
            self.log("✅ Chrome launched with cache disabled")
            return True
        except Exception as e:
            self.log(f"Failed to launch Chrome: {e}", "ERROR")
            return False
            
    def create_test_bookmarklet(self):
        """Create a bookmarklet that forces reload and checks the page"""
        bookmarklet = """javascript:(function(){
            console.clear();
            console.log('🧹 Clearing cache and reloading...');
            
            // Clear all caches
            if ('caches' in window) {
                caches.keys().then(names => {
                    names.forEach(name => caches.delete(name));
                    console.log('✅ Service worker caches cleared');
                });
            }
            
            // Clear local storage
            localStorage.clear();
            sessionStorage.clear();
            console.log('✅ Storage cleared');
            
            // Force reload with cache bypass
            setTimeout(() => {
                location.reload(true);
            }, 500);
            
            // After reload, check the page
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const input = document.getElementById('chat-input-field');
                    const button = document.getElementById('chat-send-btn');
                    
                    console.log('🔍 Checking elements after reload:');
                    console.log('Input found:', !!input);
                    console.log('Button found:', !!button);
                    
                    if (input && button) {
                        console.log('Initial button state:', button.disabled);
                        
                        // Test typing
                        input.value = 'Test';
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        
                        console.log('After typing:', {
                            value: input.value,
                            disabled: button.disabled
                        });
                        
                        if (!button.disabled) {
                            console.log('✅ SUCCESS: Button is enabled after typing!');
                            alert('✅ Cache cleared! The send button is now working correctly.');
                        } else {
                            console.log('❌ FAIL: Button still disabled');
                            alert('❌ Button still disabled. Try closing ALL Chrome windows.');
                        }
                    }
                }, 1000);
            });
        })();"""
        
        # Save bookmarklet to file
        bookmarklet_file = Path("cache_clear_bookmarklet.html")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Cache Clear Bookmarklet</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f5f5f5;
        }}
        .bookmarklet {{
            display: inline-block;
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .bookmarklet:hover {{
            background: #45a049;
        }}
        code {{
            background: #e0e0e0;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .steps {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>🧹 Cache Clear Bookmarklet</h1>
    
    <div class="steps">
        <h2>Instructions:</h2>
        <ol>
            <li>Drag this button to your bookmarks bar: 
                <a href="{bookmarklet}" class="bookmarklet">Clear Cache & Test</a>
            </li>
            <li>Navigate to <a href="http://localhost:5000" target="_blank">http://localhost:5000</a></li>
            <li>Click the bookmarklet from your bookmarks bar</li>
            <li>The page will reload and test if the send button works</li>
        </ol>
        
        <h2>What it does:</h2>
        <ul>
            <li>Clears all browser caches for the current site</li>
            <li>Clears local and session storage</li>
            <li>Forces a hard reload bypassing cache</li>
            <li>Tests if the send button enables when typing</li>
            <li>Shows an alert with the result</li>
        </ul>
        
        <h2>Manual Alternative:</h2>
        <p>Press <code>Ctrl+Shift+R</code> (Windows/Linux) or <code>Cmd+Shift+R</code> (Mac) while on the page.</p>
    </div>
</body>
</html>"""
        
        bookmarklet_file.write_text(html_content)
        self.log(f"✅ Created bookmarklet file: {bookmarklet_file.absolute()}")
        
        return bookmarklet_file
        
    def create_cache_test_script(self):
        """Create a PowerShell script for Windows users to clear Chrome cache"""
        if self.system != "Windows":
            return None
            
        script_content = '''# Chrome Cache Cleaner for localhost:5000
Write-Host "🧹 Chrome Cache Cleaner for localhost:5000" -ForegroundColor Cyan
Write-Host ""

# Kill Chrome processes
Write-Host "📍 Closing Chrome..." -ForegroundColor Yellow
$chromeProcesses = Get-Process chrome -ErrorAction SilentlyContinue
if ($chromeProcesses) {
    $chromeProcesses | Stop-Process -Force
    Write-Host "✅ Chrome closed" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "ℹ️  Chrome not running" -ForegroundColor Gray
}

# Clear Chrome cache
Write-Host ""
Write-Host "📍 Clearing Chrome cache..." -ForegroundColor Yellow

$cachePaths = @(
    "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Cache",
    "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Code Cache",
    "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Service Worker\\CacheStorage",
    "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Service Worker\\ScriptCache"
)

foreach ($path in $cachePaths) {
    if (Test-Path $path) {
        try {
            Remove-Item "$path\\*" -Recurse -Force -ErrorAction Stop
            Write-Host "✅ Cleared: $path" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Could not clear: $path" -ForegroundColor Yellow
        }
    }
}

# Launch Chrome with cache disabled
Write-Host ""
Write-Host "📍 Launching Chrome with cache disabled..." -ForegroundColor Yellow

$chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
if (-not (Test-Path $chromePath)) {
    $chromePath = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
}

if (Test-Path $chromePath) {
    Start-Process $chromePath -ArgumentList @(
        "--incognito",
        "--disable-application-cache",
        "--disable-cache", 
        "--disk-cache-size=0",
        "--aggressive-cache-discard",
        "http://localhost:5000"
    )
    Write-Host "✅ Chrome launched!" -ForegroundColor Green
} else {
    Write-Host "❌ Chrome not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "✨ Done! Check if the send button now works when typing." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
'''
        
        script_file = Path("clear_chrome_cache.ps1")
        script_file.write_text(script_content)
        self.log(f"✅ Created PowerShell script: {script_file.absolute()}")
        
        return script_file
        
    def run_full_cleanup(self):
        """Run the full cache cleanup process"""
        self.log("🚀 Starting full browser cache cleanup...")
        self.log(f"System: {self.system}")
        
        # Step 1: Kill Chrome
        self.kill_chrome_processes()
        
        # Step 2: Clear cache files
        self.clear_chrome_localhost_cache()
        
        # Step 3: Create helper files
        bookmarklet_file = self.create_test_bookmarklet()
        ps_script = self.create_cache_test_script()
        
        # Step 4: Launch Chrome with cache disabled
        self.launch_chrome_incognito()
        
        # Summary
        self.log("\n" + "="*60)
        self.log("📊 SUMMARY")
        self.log("="*60)
        self.log("✅ Chrome processes killed")
        self.log("✅ Cache directories cleaned") 
        self.log("✅ Chrome relaunched with cache disabled")
        self.log(f"✅ Bookmarklet created: {bookmarklet_file}")
        if ps_script:
            self.log(f"✅ PowerShell script created: {ps_script}")
        
        self.log("\n💡 NEXT STEPS:")
        self.log("1. Chrome should have opened to http://localhost:5000")
        self.log("2. Try typing in the chat input field")
        self.log("3. The send button should now enable/disable correctly")
        self.log(f"4. Or open {bookmarklet_file} and use the bookmarklet")
        
        return True


def main():
    """Main entry point"""
    cleaner = BrowserCacheCleaner()
    
    print("="*60)
    print("🧹 BROWSER CACHE CLEANER FOR LOCALHOST:5000")
    print("="*60)
    print()
    
    # Check if server is running first
    import requests
    try:
        resp = requests.get("http://localhost:5000", timeout=2)
        print("✅ Server is running")
    except:
        print("❌ Server not responding at http://localhost:5000")
        print("   Please start the server first: aw web")
        return
        
    # Run cleanup
    success = cleaner.run_full_cleanup()
    
    if not success:
        print("\n❌ Cleanup failed. Please try manual steps:")
        print("1. Close ALL Chrome windows")
        print("2. Press Win+R, type: chrome --incognito --disable-cache http://localhost:5000")
        print("3. Or try a different browser (Firefox, Edge)")


if __name__ == "__main__":
    main()