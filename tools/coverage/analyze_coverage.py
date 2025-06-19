#!/usr/bin/env python3
"""
Simple coverage analysis to identify which lib files need tests.
"""

import os
import glob
from pathlib import Path

def find_lib_files():
    """Find all Python files in the lib directory."""
    lib_files = []
    for root, dirs, files in os.walk('lib'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                lib_files.append(os.path.join(root, file))
    return sorted(lib_files)

def find_test_files():
    """Find all test files and extract what they're testing."""
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    return sorted(test_files)

def analyze_test_coverage():
    """Analyze which lib files have corresponding tests."""
    lib_files = find_lib_files()
    test_files = find_test_files()
    
    # Extract module names from test files
    tested_modules = set()
    for test_file in test_files:
        # Extract module name from test file
        basename = os.path.basename(test_file)
        if basename.startswith('test_'):
            module_name = basename[5:-3]  # Remove 'test_' prefix and '.py' suffix
            tested_modules.add(module_name)
    
    print("=== COVERAGE ANALYSIS ===\n")
    
    print("📁 LIB FILES FOUND:")
    covered_files = []
    uncovered_files = []
    
    for lib_file in lib_files:
        # Extract module name from lib file
        relative_path = lib_file.replace('lib/', '').replace('/', '_')
        module_name = os.path.basename(lib_file)[:-3]  # Remove .py
        
        # Check if there's a test for this module
        has_test = False
        for tested in tested_modules:
            if tested == module_name or module_name in tested or tested in module_name:
                has_test = True
                break
        
        if has_test:
            covered_files.append(lib_file)
            print(f"✅ {lib_file}")
        else:
            uncovered_files.append(lib_file)
            print(f"❌ {lib_file}")
    
    print(f"\n📊 SUMMARY:")
    print(f"Total lib files: {len(lib_files)}")
    print(f"Files with tests: {len(covered_files)} ({len(covered_files)/len(lib_files)*100:.1f}%)")
    print(f"Files without tests: {len(uncovered_files)} ({len(uncovered_files)/len(lib_files)*100:.1f}%)")
    
    if uncovered_files:
        print(f"\n🎯 FILES NEEDING TESTS:")
        for file in uncovered_files:
            print(f"   - {file}")
    
    print(f"\n🧪 TEST FILES FOUND:")
    for test_file in test_files:
        print(f"   - {test_file}")

if __name__ == "__main__":
    analyze_test_coverage()