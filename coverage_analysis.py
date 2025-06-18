#!/usr/bin/env python3
"""
Simple coverage analysis script to map library files to test files
"""

import os
from pathlib import Path

def main():
    # Get library files
    lib_files = []
    for root, dirs, files in os.walk('lib'):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                lib_files.append(os.path.join(root, file))

    # Get test files
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))

    print(f'Library files: {len(lib_files)}')
    print(f'Test files: {len(test_files)}')

    # Map lib files to tests
    coverage_report = []
    for lib_file in sorted(lib_files):
        lib_name = Path(lib_file).stem
        # Look for corresponding test
        test_found = False
        test_file_found = None
        for test_file in test_files:
            if lib_name in test_file:
                test_found = True
                test_file_found = test_file
                break
        coverage_report.append((lib_file, test_found, test_file_found))

    print(f'\nTest Coverage Analysis:')
    print('='*80)
    covered = 0
    for lib_file, has_test, test_file in coverage_report:
        status = '✓' if has_test else '✗'
        test_info = test_file if test_file else "NO TEST"
        print(f'{status} {lib_file:40} -> {test_info}')
        if has_test:
            covered += 1

    print(f'\nSummary:')
    print(f'Files with tests: {covered}/{len(lib_files)} ({covered/len(lib_files)*100:.1f}%)')
    print(f'Files without tests: {len(lib_files)-covered}')
    
    # List files without tests
    print(f'\nFiles without tests:')
    for lib_file, has_test, _ in coverage_report:
        if not has_test:
            print(f'  - {lib_file}')

if __name__ == '__main__':
    main()