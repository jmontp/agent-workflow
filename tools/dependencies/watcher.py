#!/usr/bin/env python3
"""
Dependency Watcher - Real-time File Change Monitoring

Monitors file changes in the codebase and triggers automatic updates
based on dependency mappings. Integrates with the tracker to identify
which files need to be updated when a change is detected.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from datetime import datetime
from collections import defaultdict
import yaml

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
except ImportError:
    print("watchdog not installed. Install with: pip install watchdog")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.dependencies.tracker import DependencyTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DependencyEventHandler(FileSystemEventHandler):
    """Handle file system events and trigger dependency updates"""
    
    def __init__(self, tracker: DependencyTracker, update_handler: Callable):
        self.tracker = tracker
        self.update_handler = update_handler
        self.ignore_patterns = {
            '__pycache__', '.git', '.pytest_cache', 'venv',
            'env', 'build', 'dist', '*.egg-info', 'htmlcov',
            'site', '.tox', 'node_modules', '.orch-state'
        }
        self._pending_updates = defaultdict(set)
        self._update_lock = asyncio.Lock()
        
    def should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed"""
        path_str = str(file_path)
        
        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return False
        
        # Check file extensions
        valid_extensions = {'.py', '.md', '.yaml', '.yml', '.json', '.toml'}
        return any(path_str.endswith(ext) for ext in valid_extensions)
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory or not self.should_process_file(event.src_path):
            return
        
        self._handle_file_change(event.src_path, 'modified')
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory or not self.should_process_file(event.src_path):
            return
        
        self._handle_file_change(event.src_path, 'created')
    
    def _handle_file_change(self, file_path: str, change_type: str):
        """Process file changes and queue updates"""
        try:
            # Get relative path
            rel_path = self.tracker._get_relative_path(Path(file_path))
            
            logger.info(f"File {change_type}: {rel_path}")
            
            # Find related files
            related = self.tracker.find_related_files(rel_path)
            
            if related:
                # Queue updates for related files
                self._pending_updates[rel_path].update({
                    'change_type': change_type,
                    'timestamp': datetime.now(),
                    'related_files': related
                })
                
                # Trigger update handler asynchronously
                asyncio.create_task(self._trigger_updates(rel_path, related, change_type))
            
        except Exception as e:
            logger.error(f"Error handling file change: {e}")
    
    async def _trigger_updates(self, source_file: str, related_files: Dict[str, List[str]], change_type: str):
        """Trigger updates for related files"""
        async with self._update_lock:
            try:
                await self.update_handler(source_file, related_files, change_type)
            except Exception as e:
                logger.error(f"Error triggering updates: {e}")


class DependencyWatcher:
    """
    Watches for file changes and triggers automatic dependency updates.
    
    Monitors the codebase for changes and uses dependency mappings to
    determine which files need to be updated when a file is modified.
    """
    
    def __init__(self, project_root: Path, config_path: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.tracker = DependencyTracker(self.project_root)
        self.observer = Observer()
        self.config = self._load_config(config_path)
        self.update_queue = asyncio.Queue()
        self.update_handlers = []
        self._running = False
        
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load watcher configuration"""
        default_config = {
            'watch_patterns': ['**/*.py', '**/*.md', '**/*.yaml', '**/*.yml'],
            'ignore_patterns': ['__pycache__', '.git', 'venv', 'build', 'dist'],
            'debounce_seconds': 2.0,
            'max_concurrent_updates': 3,
            'update_strategies': {
                'test': 'update_if_exists',
                'doc': 'suggest_update',
                'import': 'check_compatibility'
            }
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def add_update_handler(self, handler: Callable) -> None:
        """Add a handler for file updates"""
        self.update_handlers.append(handler)
    
    async def start(self) -> None:
        """Start watching for file changes"""
        logger.info(f"Starting dependency watcher for: {self.project_root}")
        
        # Initial scan
        logger.info("Performing initial dependency scan...")
        self.tracker.scan_project()
        
        # Setup file system watcher
        event_handler = DependencyEventHandler(
            self.tracker,
            self._handle_dependency_update
        )
        
        self.observer.schedule(
            event_handler,
            str(self.project_root),
            recursive=True
        )
        
        self.observer.start()
        self._running = True
        
        # Start update processor
        await self._process_updates()
    
    async def stop(self) -> None:
        """Stop watching for file changes"""
        logger.info("Stopping dependency watcher...")
        self._running = False
        self.observer.stop()
        self.observer.join()
    
    async def _handle_dependency_update(self, source_file: str, related_files: Dict[str, List[str]], change_type: str):
        """Handle dependency updates"""
        update_info = {
            'source_file': source_file,
            'related_files': related_files,
            'change_type': change_type,
            'timestamp': datetime.now()
        }
        
        await self.update_queue.put(update_info)
    
    async def _process_updates(self) -> None:
        """Process queued updates with debouncing"""
        pending_updates = defaultdict(lambda: {'files': set(), 'timestamp': None})
        
        while self._running:
            try:
                # Get update with timeout
                try:
                    update = await asyncio.wait_for(
                        self.update_queue.get(),
                        timeout=self.config['debounce_seconds']
                    )
                    
                    # Add to pending updates
                    source = update['source_file']
                    pending_updates[source]['files'].update(
                        sum(update['related_files'].values(), [])
                    )
                    pending_updates[source]['timestamp'] = update['timestamp']
                    
                except asyncio.TimeoutError:
                    # Process pending updates after debounce period
                    if pending_updates:
                        await self._execute_updates(pending_updates)
                        pending_updates.clear()
                
            except Exception as e:
                logger.error(f"Error processing updates: {e}")
                await asyncio.sleep(1)
    
    async def _execute_updates(self, pending_updates: Dict[str, Dict]) -> None:
        """Execute pending updates"""
        # Limit concurrent updates
        semaphore = asyncio.Semaphore(self.config['max_concurrent_updates'])
        
        async def update_with_limit(source: str, info: Dict):
            async with semaphore:
                await self._execute_single_update(source, info)
        
        # Execute all updates concurrently
        tasks = [
            update_with_limit(source, info)
            for source, info in pending_updates.items()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_single_update(self, source_file: str, update_info: Dict) -> None:
        """Execute update for a single source file"""
        try:
            related_files = list(update_info['files'])
            
            logger.info(f"Executing updates for {source_file} affecting {len(related_files)} files")
            
            # Call all registered handlers
            for handler in self.update_handlers:
                try:
                    await handler({
                        'source_file': source_file,
                        'related_files': related_files,
                        'timestamp': update_info['timestamp'],
                        'tracker': self.tracker
                    })
                except Exception as e:
                    logger.error(f"Handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error executing update for {source_file}: {e}")
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get current dependency graph"""
        return {
            'nodes': {
                path: node.to_dict()
                for path, node in self.tracker.file_nodes.items()
            },
            'edges': [
                dep.to_dict()
                for dep in self.tracker.dependencies
            ]
        }
    
    def get_update_suggestions(self, file_path: str) -> Dict[str, List[str]]:
        """Get update suggestions for a specific file"""
        related = self.tracker.find_related_files(file_path)
        
        suggestions = {
            'must_update': [],
            'should_update': [],
            'consider_updating': []
        }
        
        # Categorize by importance
        if 'tests' in related:
            suggestions['must_update'].extend(related['tests'])
        
        if 'docs' in related:
            suggestions['should_update'].extend(related['docs'])
        
        if 'code' in related:
            # Filter out the file itself
            deps = [f for f in related['code'] if f != file_path]
            if deps:
                suggestions['consider_updating'].extend(deps)
        
        return {k: v for k, v in suggestions.items() if v}


async def example_update_handler(update_info: Dict[str, Any]) -> None:
    """Example update handler that logs update information"""
    source = update_info['source_file']
    related = update_info['related_files']
    
    logger.info(f"Update handler called for: {source}")
    logger.info(f"  Related files: {related}")
    
    # Example: Generate update commands
    if source.endswith('.py'):
        # Code file changed
        for test_file in [f for f in related if 'test' in f]:
            logger.info(f"  → Update test: {test_file}")
        
        for doc_file in [f for f in related if f.endswith('.md')]:
            logger.info(f"  → Update docs: {doc_file}")
    
    elif source.endswith('.md'):
        # Documentation changed
        logger.info("  → Validate code references in documentation")


async def main():
    """Main entry point for the watcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Watch for file changes and track dependencies')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(),
                        help='Project root directory')
    parser.add_argument('--config', type=Path, help='Configuration file')
    parser.add_argument('--export-graph', action='store_true',
                        help='Export dependency graph and exit')
    
    args = parser.parse_args()
    
    watcher = DependencyWatcher(args.project_root, args.config)
    
    if args.export_graph:
        # Just export the graph
        watcher.tracker.scan_project()
        graph = watcher.get_dependency_graph()
        
        output_file = args.project_root / 'dependency_graph.json'
        import json
        with open(output_file, 'w') as f:
            json.dump(graph, f, indent=2)
        
        logger.info(f"Exported dependency graph to {output_file}")
        return
    
    # Add example handler
    watcher.add_update_handler(example_update_handler)
    
    try:
        # Start watching
        await watcher.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await watcher.stop()


if __name__ == '__main__':
    asyncio.run(main())