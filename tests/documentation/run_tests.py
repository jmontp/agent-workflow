#!/usr/bin/env python3
"""
Quick runner for documentation tests.

This script provides an easy way to run documentation validation tests
without needing to remember pytest command syntax.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run documentation tests with helpful output."""
    test_dir = Path(__file__).parent
    
    print("🔍 Running Documentation Example Validation Tests...")
    print("=" * 60)
    
    try:
        # Run tests with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_dir / "test_documentation_examples.py"),
            "-v", "--tb=short"
        ], cwd=test_dir.parent.parent)
        
        if result.returncode == 0:
            print("\n✅ All documentation tests passed!")
            print("\nThese tests validate:")
            print("  • Python code examples can be parsed")
            print("  • YAML configuration syntax is valid")  
            print("  • CLI commands are properly formatted")
            print("  • Critical internal links work")
            print("  • Environment variable formats are correct")
        else:
            print("\n❌ Some documentation tests failed!")
            print("Check the output above for details.")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ Error: pytest not found. Install with: pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())