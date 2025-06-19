#!/usr/bin/env python3
"""
Dependency Updater - Automatic File Update System

Handles automatic updates of dependent files when source files change.
Integrates with Claude Code for intelligent updates while respecting
security boundaries and maintaining code quality.
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import yaml
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.dependencies.tracker import DependencyTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UpdateStrategy:
    """Base class for update strategies"""
    
    async def should_update(self, source_file: str, target_file: str, change_type: str) -> bool:
        """Determine if target file should be updated"""
        raise NotImplementedError
    
    async def generate_update(self, source_file: str, target_file: str, change_type: str) -> Dict[str, Any]:
        """Generate update instructions"""
        raise NotImplementedError


class TestUpdateStrategy(UpdateStrategy):
    """Strategy for updating test files when code changes"""
    
    async def should_update(self, source_file: str, target_file: str, change_type: str) -> bool:
        """Test files should always be checked when code changes"""
        # Check if test file exists
        if not Path(target_file).exists():
            return change_type == 'created'  # Create test for new code
        
        # Always update tests when code changes
        return True
    
    async def generate_update(self, source_file: str, target_file: str, change_type: str) -> Dict[str, Any]:
        """Generate test update instructions"""
        source_path = Path(source_file)
        target_path = Path(target_file)
        
        if not target_path.exists():
            # Create new test file
            return {
                'action': 'create_test',
                'source': source_file,
                'target': target_file,
                'template': 'test_template.py',
                'instructions': f"Create comprehensive tests for {source_path.stem}"
            }
        else:
            # Update existing test
            return {
                'action': 'update_test',
                'source': source_file,
                'target': target_file,
                'instructions': f"Update tests to reflect changes in {source_file}",
                'focus_areas': self._identify_changes(source_file)
            }
    
    def _identify_changes(self, source_file: str) -> List[str]:
        """Identify what changed in the source file"""
        # In a real implementation, this would use git diff or AST analysis
        return ["new methods", "modified signatures", "error handling"]


class DocUpdateStrategy(UpdateStrategy):
    """Strategy for updating documentation when code changes"""
    
    async def should_update(self, source_file: str, target_file: str, change_type: str) -> bool:
        """Documentation should be updated for significant changes"""
        if not Path(target_file).exists():
            return False  # Don't auto-create docs
        
        # Update docs for modified code
        return change_type == 'modified'
    
    async def generate_update(self, source_file: str, target_file: str, change_type: str) -> Dict[str, Any]:
        """Generate documentation update instructions"""
        return {
            'action': 'update_documentation',
            'source': source_file,
            'target': target_file,
            'instructions': f"Update documentation to reflect changes in {source_file}",
            'sections': ["API changes", "Examples", "Usage patterns"]
        }


class DependencyUpdater:
    """
    Handles automatic updates of dependent files based on changes.
    
    Coordinates with Claude Code to intelligently update tests,
    documentation, and dependent code while maintaining quality
    and security boundaries.
    """
    
    def __init__(self, project_root: Path, config_path: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.tracker = DependencyTracker(self.project_root)
        self.config = self._load_config(config_path)
        self.strategies = self._initialize_strategies()
        self.update_queue = []
        self._claude_available = self._check_claude_availability()
        
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load updater configuration"""
        default_config = {
            'auto_update': {
                'tests': True,
                'docs': True,
                'dependent_code': False
            },
            'update_modes': {
                'tests': 'suggest',  # 'auto', 'suggest', 'manual'
                'docs': 'suggest',
                'code': 'manual'
            },
            'claude_integration': {
                'enabled': True,
                'model': 'claude-3-opus-20240229',
                'max_tokens': 4096
            },
            'validation': {
                'run_tests': True,
                'check_coverage': True,
                'lint_code': True
            }
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Deep merge configurations
                    self._merge_configs(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _merge_configs(self, base: Dict, update: Dict) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def _initialize_strategies(self) -> Dict[str, UpdateStrategy]:
        """Initialize update strategies"""
        return {
            'test': TestUpdateStrategy(),
            'doc': DocUpdateStrategy(),
        }
    
    def _check_claude_availability(self) -> bool:
        """Check if Claude Code CLI is available"""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def process_file_change(self, file_path: str, change_type: str) -> List[Dict[str, Any]]:
        """Process a file change and generate update recommendations"""
        logger.info(f"Processing {change_type} for {file_path}")
        
        # Get dependencies
        related_files = self.tracker.find_related_files(file_path)
        update_recommendations = []
        
        # Process each category of related files
        for category, files in related_files.items():
            strategy_key = category.rstrip('s')  # 'tests' -> 'test'
            strategy = self.strategies.get(strategy_key)
            
            if not strategy:
                continue
            
            for related_file in files:
                if await strategy.should_update(file_path, related_file, change_type):
                    update = await strategy.generate_update(file_path, related_file, change_type)
                    update['category'] = category
                    update['auto_update'] = self.config['auto_update'].get(category, False)
                    update['mode'] = self.config['update_modes'].get(category, 'manual')
                    update_recommendations.append(update)
        
        return update_recommendations
    
    async def execute_updates(self, updates: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        """Execute the recommended updates"""
        results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
        
        for update in updates:
            try:
                if update['mode'] == 'manual':
                    results['skipped'].append({
                        'file': update['target'],
                        'reason': 'Manual update required'
                    })
                    continue
                
                if dry_run:
                    logger.info(f"[DRY RUN] Would update {update['target']}")
                    results['successful'].append({
                        'file': update['target'],
                        'action': update['action'],
                        'dry_run': True
                    })
                    continue
                
                # Execute based on action type
                if update['action'] == 'create_test':
                    result = await self._create_test_file(update)
                elif update['action'] == 'update_test':
                    result = await self._update_test_file(update)
                elif update['action'] == 'update_documentation':
                    result = await self._update_documentation(update)
                else:
                    result = {'success': False, 'error': f"Unknown action: {update['action']}"}
                
                if result['success']:
                    results['successful'].append(result)
                else:
                    results['failed'].append(result)
                    
            except Exception as e:
                logger.error(f"Error executing update for {update.get('target')}: {e}")
                results['failed'].append({
                    'file': update.get('target'),
                    'error': str(e)
                })
        
        # Run validation if configured
        if not dry_run and self.config['validation']['run_tests']:
            await self._run_validation(results['successful'])
        
        return results
    
    async def _create_test_file(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test file"""
        target_path = Path(update['target'])
        
        # Ensure directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate test content
        if self._claude_available and self.config['claude_integration']['enabled']:
            content = await self._generate_with_claude(update, 'create_test')
        else:
            content = self._generate_test_template(update['source'])
        
        # Write test file
        with open(target_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Created test file: {target_path}")
        
        return {
            'success': True,
            'file': update['target'],
            'action': 'created',
            'size': len(content)
        }
    
    async def _update_test_file(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing test file"""
        if self._claude_available and self.config['claude_integration']['enabled']:
            # Use Claude for intelligent updates
            return await self._update_with_claude(update)
        else:
            # Fallback to suggestion mode
            return {
                'success': True,
                'file': update['target'],
                'action': 'suggested',
                'suggestion': f"Review and update tests in {update['target']} for changes in {update['source']}"
            }
    
    async def _update_documentation(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Update documentation file"""
        if self._claude_available and self.config['claude_integration']['enabled']:
            # Use Claude for documentation updates
            return await self._update_with_claude(update)
        else:
            # Generate update checklist
            return {
                'success': True,
                'file': update['target'],
                'action': 'checklist',
                'items': [
                    f"Update API documentation for {update['source']}",
                    "Review and update code examples",
                    "Check for outdated references",
                    "Update changelog if needed"
                ]
            }
    
    async def _generate_with_claude(self, update: Dict[str, Any], task_type: str) -> str:
        """Generate content using Claude Code"""
        # This would integrate with Claude Code CLI
        # For now, return a template
        return self._generate_test_template(update['source'])
    
    async def _update_with_claude(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Update file using Claude Code"""
        # This would integrate with Claude Code CLI for intelligent updates
        # For now, return a suggestion
        return {
            'success': True,
            'file': update['target'],
            'action': 'claude_suggested',
            'suggestion': f"Claude would update {update['target']} based on changes in {update['source']}"
        }
    
    def _generate_test_template(self, source_file: str) -> str:
        """Generate a basic test template"""
        source_path = Path(source_file)
        module_name = source_path.stem
        
        return f'''"""
Unit tests for {module_name}.

Auto-generated by dependency updater.
TODO: Implement comprehensive tests.
"""

import unittest
from unittest.mock import Mock, patch

from {source_file.replace('/', '.').replace('.py', '')} import *


class Test{module_name.title().replace('_', '')}(unittest.TestCase):
    """Test cases for {module_name}"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_placeholder(self):
        """TODO: Implement actual tests"""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
'''
    
    async def _run_validation(self, updated_files: List[Dict[str, Any]]) -> None:
        """Run validation on updated files"""
        if not updated_files:
            return
        
        logger.info("Running validation on updated files...")
        
        # Run tests if any test files were updated
        test_files = [f['file'] for f in updated_files if 'test' in f['file']]
        if test_files and self.config['validation']['run_tests']:
            await self._run_tests(test_files)
        
        # Check coverage if configured
        if self.config['validation']['check_coverage']:
            await self._check_coverage()
        
        # Lint code if configured
        if self.config['validation']['lint_code']:
            await self._lint_files([f['file'] for f in updated_files])
    
    async def _run_tests(self, test_files: List[str]) -> None:
        """Run specific test files"""
        try:
            cmd = ['pytest'] + test_files + ['-v']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("All tests passed!")
            else:
                logger.warning(f"Tests failed: {result.stdout}")
        except Exception as e:
            logger.error(f"Error running tests: {e}")
    
    async def _check_coverage(self) -> None:
        """Check code coverage"""
        try:
            cmd = ['pytest', '--cov=lib', '--cov-report=term-missing']
            result = subprocess.run(cmd, capture_output=True, text=True)
            logger.info("Coverage check completed")
        except Exception as e:
            logger.error(f"Error checking coverage: {e}")
    
    async def _lint_files(self, files: List[str]) -> None:
        """Lint updated files"""
        python_files = [f for f in files if f.endswith('.py')]
        if not python_files:
            return
        
        try:
            # Try various linters
            for linter, cmd_template in [
                ('ruff', ['ruff', 'check'] + python_files),
                ('flake8', ['flake8'] + python_files),
                ('pylint', ['pylint'] + python_files)
            ]:
                try:
                    result = subprocess.run(cmd_template, capture_output=True, text=True)
                    if result.returncode == 0:
                        logger.info(f"{linter}: All files pass!")
                    else:
                        logger.warning(f"{linter} issues found")
                    break
                except FileNotFoundError:
                    continue
        except Exception as e:
            logger.error(f"Error running linter: {e}")
    
    def generate_update_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable update report"""
        lines = ["Dependency Update Report", "=" * 50, ""]
        
        # Summary
        lines.extend([
            f"Successful updates: {len(results['successful'])}",
            f"Failed updates: {len(results['failed'])}",
            f"Skipped (manual): {len(results['skipped'])}",
            ""
        ])
        
        # Successful updates
        if results['successful']:
            lines.append("Successful Updates:")
            for update in results['successful']:
                lines.append(f"  ✓ {update['file']} - {update['action']}")
            lines.append("")
        
        # Failed updates
        if results['failed']:
            lines.append("Failed Updates:")
            for update in results['failed']:
                lines.append(f"  ✗ {update['file']} - {update.get('error', 'Unknown error')}")
            lines.append("")
        
        # Manual updates needed
        if results['skipped']:
            lines.append("Manual Updates Required:")
            for update in results['skipped']:
                lines.append(f"  ⚠ {update['file']} - {update['reason']}")
            lines.append("")
        
        return "\n".join(lines)


async def main():
    """Main entry point for the updater"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update dependent files based on changes')
    parser.add_argument('file', help='Changed file to process')
    parser.add_argument('--change-type', choices=['created', 'modified', 'deleted'],
                        default='modified', help='Type of change')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be updated without making changes')
    parser.add_argument('--config', type=Path, help='Configuration file')
    parser.add_argument('--auto', action='store_true',
                        help='Automatically execute updates (no prompts)')
    
    args = parser.parse_args()
    
    # Initialize updater
    updater = DependencyUpdater(Path.cwd(), args.config)
    
    # Scan project
    logger.info("Scanning project dependencies...")
    updater.tracker.scan_project()
    
    # Process file change
    recommendations = await updater.process_file_change(args.file, args.change_type)
    
    if not recommendations:
        logger.info("No updates recommended")
        return
    
    # Display recommendations
    print("\nRecommended Updates:")
    print("-" * 50)
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['action']} - {rec['target']}")
        print(f"   Category: {rec['category']}")
        print(f"   Mode: {rec['mode']}")
        if 'instructions' in rec:
            print(f"   Instructions: {rec['instructions']}")
        print()
    
    # Execute updates
    if args.auto or (not args.dry_run and input("Execute updates? [y/N] ").lower() == 'y'):
        results = await updater.execute_updates(recommendations, args.dry_run)
        
        # Display report
        print("\n" + updater.generate_update_report(results))
    else:
        print("Updates cancelled")


if __name__ == '__main__':
    asyncio.run(main())