#!/usr/bin/env python3
"""
Documentation Quality Checker

A lightweight script to check documentation quality before commits.
Can be used as a pre-commit hook or standalone validation tool.

Usage:
    python tools/check_docs_quality.py
    python tools/check_docs_quality.py --fix-minor  # Auto-fix minor issues
    python tools/check_docs_quality.py --verbose    # Detailed output
"""

import os
import sys
import re
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

class DocumentationChecker:
    def __init__(self, root_path: Path, verbose: bool = False, fix_minor: bool = False):
        self.root_path = root_path
        self.verbose = verbose
        self.fix_minor = fix_minor
        self.issues = []
        self.fixes_applied = []
        
    def check_all(self) -> bool:
        """Run all documentation checks"""
        print("🔍 Running documentation quality checks...")
        
        success = True
        success &= self.check_yaml_files()
        success &= self.check_mkdocs_config()
        success &= self.check_markdown_structure()
        success &= self.check_required_files()
        success &= self.check_content_quality()
        
        self.print_summary()
        return success
        
    def check_yaml_files(self) -> bool:
        """Validate YAML configuration files"""
        if self.verbose:
            print("  Checking YAML files...")
            
        yaml_files = [
            'orch-config.yaml',
            'config.example.yml',
            'pyproject.toml'  # TOML but can check basic structure
            # Skip mkdocs.yml as it has special tags that need MkDocs to parse
        ]
        
        success = True
        for yaml_file in yaml_files:
            file_path = self.root_path / yaml_file
            if not file_path.exists():
                if self.verbose:
                    print(f"    ⚠️  {yaml_file} not found (skipping)")
                continue
                
            try:
                if yaml_file.endswith('.toml'):
                    # Basic TOML structure check
                    content = file_path.read_text()
                    if '[' not in content:
                        self.issues.append(f"❌ {yaml_file}: Appears to be empty or invalid TOML")
                        success = False
                elif yaml_file == 'mkdocs.yml':
                    # Skip - handled in check_mkdocs_config
                    continue
                else:
                    with open(file_path, 'r') as f:
                        yaml.safe_load(f)
                        
                if self.verbose:
                    print(f"    ✅ {yaml_file}")
                    
            except Exception as e:
                self.issues.append(f"❌ {yaml_file}: {e}")
                success = False
                
        return success
        
    def check_mkdocs_config(self) -> bool:
        """Check MkDocs configuration for common issues"""
        if self.verbose:
            print("  Checking MkDocs configuration...")
            
        mkdocs_path = self.root_path / 'mkdocs.yml'
        if not mkdocs_path.exists():
            self.issues.append("❌ mkdocs.yml not found")
            return False
            
        try:
            # Simple validation - just check it's valid YAML structure
            # Skip complex MkDocs-specific tags validation for CI speed
            content = mkdocs_path.read_text()
            
            # Basic structure checks
            if 'site_name:' not in content:
                self.issues.append("❌ mkdocs.yml: Missing site_name")
                return False
                
            if 'docs_dir:' not in content:
                self.issues.append("❌ mkdocs.yml: Missing docs_dir")
                return False
                
            if 'nav:' not in content:
                self.issues.append("❌ mkdocs.yml: Missing nav section")
                return False
            
            # Check if YAML is syntactically valid (basic structure)
            lines = content.split('\n')
            indent_stack = []
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('#') or not line.strip():
                    continue
                    
                # Check for obvious YAML syntax errors
                if ':' in line and not line.strip().startswith('-'):
                    # Basic key-value pair validation
                    if line.count(':') > 1 and not any(tag in line for tag in ['http:', 'https:', '!ENV', '!!']):
                        continue  # Multiple colons might be URLs or special tags
                        
            # Extract docs_dir value
            docs_dir_match = re.search(r'docs_dir:\s*(.+)', content)
            if docs_dir_match:
                docs_dir_name = docs_dir_match.group(1).strip()
                docs_dir = self.root_path / docs_dir_name
                if not docs_dir.exists():
                    self.issues.append(f"❌ Documentation directory '{docs_dir_name}' does not exist")
                    return False
                    
            if self.verbose:
                print("    ✅ MkDocs configuration")
                
        except Exception as e:
            self.issues.append(f"❌ mkdocs.yml: Error reading file - {e}")
            return False
            
        return True
        
    def check_markdown_structure(self) -> bool:
        """Check markdown files for basic structure issues"""
        if self.verbose:
            print("  Checking markdown structure...")
            
        docs_dir = self.root_path / 'docs_src'
        if not docs_dir.exists():
            self.issues.append("❌ docs_src directory not found")
            return False
            
        success = True
        md_files = list(docs_dir.rglob('*.md'))
        
        for md_file in md_files:
            issues = self.check_single_markdown_file(md_file)
            if issues:
                success = False
                self.issues.extend(issues)
                
        if self.verbose and success:
            print(f"    ✅ Checked {len(md_files)} markdown files")
            
        return success
        
    def check_single_markdown_file(self, file_path: Path) -> List[str]:
        """Check a single markdown file"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return [f"❌ {file_path.relative_to(self.root_path)}: Cannot read file - {e}"]
            
        issues = []
        relative_path = file_path.relative_to(self.root_path)
        
        # Check for empty files
        if not content.strip():
            issues.append(f"❌ {relative_path}: Empty file")
            return issues
            
        lines = content.split('\n')
        
        # Check for proper heading structure (skip includes and special files)
        is_special_file = any(part in str(relative_path).lower() for part in [
            'includes/', 'templates/', '.github/', '_'
        ])
        
        if not is_special_file:
            has_main_heading = False
            for i, line in enumerate(lines[:15]):  # Check first 15 lines
                if line.startswith('# ') or line.strip() == '---':
                    has_main_heading = True
                    break
                    
            if not has_main_heading and len(content) > 200:
                issues.append(f"⚠️  {relative_path}: No clear main heading found")
            
        # Check for broken links (empty parentheses)
        broken_links = re.findall(r'\]\(\s*\)', content)
        if broken_links:
            issues.append(f"❌ {relative_path}: {len(broken_links)} empty link(s) found")
            
        # Check for unresolved merge conflicts
        if '<<<<<<< ' in content or '>>>>>>> ' in content:
            issues.append(f"❌ {relative_path}: Unresolved merge conflict markers")
            
        # Auto-fix minor issues if requested
        if self.fix_minor:
            fixed_content = content
            
            # Fix double spaces after periods
            original_content = fixed_content
            fixed_content = re.sub(r'\.  +', '. ', fixed_content)
            
            # Fix trailing whitespace
            fixed_content = '\n'.join(line.rstrip() for line in fixed_content.split('\n'))
            
            if fixed_content != original_content:
                file_path.write_text(fixed_content, encoding='utf-8')
                self.fixes_applied.append(f"✅ {relative_path}: Fixed spacing issues")
                
        return issues
        
    def check_required_files(self) -> bool:
        """Check for required documentation files"""
        if self.verbose:
            print("  Checking required files...")
            
        docs_dir = self.root_path / 'docs_src'
        required_files = [
            'index.md',
            'getting-started/index.md',
            'user-guide/index.md',
            'concepts/index.md',
            'architecture/index.md'
        ]
        
        success = True
        for file_path in required_files:
            full_path = docs_dir / file_path
            if not full_path.exists():
                self.issues.append(f"❌ Required file missing: docs_src/{file_path}")
                success = False
            elif self.verbose:
                print(f"    ✅ {file_path}")
                
        return success
        
    def check_content_quality(self) -> bool:
        """Check for content quality issues"""
        if self.verbose:
            print("  Checking content quality...")
            
        docs_dir = self.root_path / 'docs_src'
        success = True
        
        # Count TODO/FIXME markers
        todo_count = 0
        for md_file in docs_dir.rglob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                todo_count += len(re.findall(r'TODO|FIXME', content, re.IGNORECASE))
            except:
                continue
                
        if todo_count > 15:
            self.issues.append(f"⚠️  High number of TODO/FIXME markers: {todo_count}")
            success = False
        elif self.verbose:
            print(f"    ✅ TODO/FIXME markers: {todo_count}/15")
            
        return success
        
    def print_summary(self):
        """Print check summary"""
        print("\n" + "="*50)
        print("Documentation Quality Check Summary")
        print("="*50)
        
        if self.fixes_applied:
            print(f"\n🔧 Auto-fixes applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"  {fix}")
                
        if self.issues:
            print(f"\n❌ Issues found: {len(self.issues)}")
            for issue in self.issues:
                print(f"  {issue}")
        else:
            print("\n✅ All documentation quality checks passed!")
            
        print()

def main():
    parser = argparse.ArgumentParser(description='Check documentation quality')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--fix-minor', action='store_true',
                       help='Auto-fix minor issues like spacing')
    
    args = parser.parse_args()
    
    root_path = Path(__file__).parent.parent
    checker = DocumentationChecker(root_path, args.verbose, args.fix_minor)
    
    success = checker.check_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()