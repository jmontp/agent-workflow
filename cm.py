#!/usr/bin/env python3
"""
Context Manager CLI - Quick command-line interface for context operations.

Usage:
    cm log-decision "decision" "reasoning"
    cm log-error "error message" 
    cm suggest
    cm stats
    cm query [--type TYPE] [--since HOURS] [--limit N] [query_text]
    cm list-projects
    cm use-project PROJECT_ID
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from context_manager import ContextManager, ContextType

# Store current project in a simple config file
CONFIG_FILE = Path.home() / ".cm_config.json"


def load_config():
    """Load CLI configuration."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"current_project": "default"}


def save_config(config):
    """Save CLI configuration."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)


def get_current_project():
    """Get current project ID."""
    config = load_config()
    return config.get("current_project", "default")


def set_current_project(project_id):
    """Set current project ID."""
    config = load_config()
    config["current_project"] = project_id
    save_config(config)


def cmd_log_decision(args):
    """Log a development decision."""
    cm = ContextManager(project_id=get_current_project())
    context_id = cm.log_decision(args.decision, args.reasoning)
    print(f"✓ Decision logged: {context_id}")
    
    # Show suggestions if any
    suggestions = cm.suggest_next_task()
    if suggestions:
        print("\n💡 Suggestions based on patterns:")
        for s in suggestions[:3]:
            print(f"  - {s['task']} (confidence: {s['confidence']:.1%})")
            print(f"    Reason: {s['reason']}")


def cmd_log_error(args):
    """Log an error."""
    cm = ContextManager(project_id=get_current_project())
    context_info = {}
    if args.context:
        try:
            context_info = json.loads(args.context)
        except:
            context_info = {"raw": args.context}
    
    context_id = cm.log_error(args.error, context_info)
    print(f"✓ Error logged: {context_id}")


def cmd_suggest(args):
    """Get task suggestions."""
    cm = ContextManager(project_id=get_current_project())
    suggestions = cm.suggest_next_task()
    
    if not suggestions:
        print("No suggestions at this time. Keep building!")
    else:
        print("📋 Task suggestions based on patterns:\n")
        for i, s in enumerate(suggestions, 1):
            print(f"{i}. {s['task']} (confidence: {s['confidence']:.1%})")
            print(f"   Reason: {s['reason']}\n")


def cmd_stats(args):
    """Show statistics."""
    cm = ContextManager(project_id=get_current_project())
    stats = cm.get_stats()
    
    print(f"📊 Context Manager Statistics (Project: {stats['project_id']})")
    print(f"   Total contexts: {stats['total_contexts']}")
    print(f"   Patterns detected: {stats['patterns_detected']}")
    print(f"   Significant patterns: {stats['significant_patterns']}")
    
    print("\n   Contexts by type:")
    for ctype, count in stats['by_type'].items():
        if count > 0:
            print(f"     - {ctype}: {count}")
    
    # Show top patterns
    patterns = cm.get_patterns(min_occurrences=2)
    if patterns:
        print("\n   Top patterns:")
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]
        for pattern, count in sorted_patterns:
            print(f"     - {pattern}: {count} occurrences")


def cmd_query(args):
    """Query contexts."""
    cm = ContextManager(project_id=get_current_project())
    
    # Build query parameters
    kwargs = {}
    if args.type:
        try:
            kwargs['context_type'] = ContextType(args.type)
        except ValueError:
            print(f"Invalid type: {args.type}")
            print(f"Valid types: {', '.join(t.value for t in ContextType)}")
            return
    
    if args.since:
        kwargs['since'] = datetime.now() - timedelta(hours=args.since)
    
    if args.limit:
        kwargs['limit'] = args.limit
    
    if args.query:
        kwargs['query'] = ' '.join(args.query)
    
    # Execute query
    results = cm.query_contexts(**kwargs)
    
    if not results:
        print("No contexts found matching criteria.")
    else:
        print(f"Found {len(results)} contexts:\n")
        for ctx in results:
            print(f"📌 {ctx.timestamp.strftime('%Y-%m-%d %H:%M')} | {ctx.type.value} | {ctx.source}")
            
            # Show relevant data based on type
            if ctx.type == ContextType.DECISION:
                print(f"   Decision: {ctx.data.get('decision', 'N/A')}")
                print(f"   Reasoning: {ctx.data.get('reasoning', 'N/A')}")
            elif ctx.type == ContextType.ERROR:
                print(f"   Error: {ctx.data.get('error', 'N/A')}")
            else:
                # Show first line of data
                data_str = str(ctx.data)
                if len(data_str) > 80:
                    data_str = data_str[:77] + "..."
                print(f"   Data: {data_str}")
            
            if ctx.tags:
                print(f"   Tags: {', '.join(ctx.tags)}")
            print()


def cmd_list_projects(args):
    """List all projects."""
    base_dir = Path("./context_store")
    current = get_current_project()
    
    if not base_dir.exists():
        print("No projects found. Create one by logging a context.")
        return
    
    print("📁 Available projects:")
    for project_dir in base_dir.iterdir():
        if project_dir.is_dir():
            marker = " (current)" if project_dir.name == current else ""
            # Count contexts
            ctx_count = len(list((project_dir / "contexts" / "active").rglob("*.json")))
            print(f"   - {project_dir.name}{marker} ({ctx_count} contexts)")


def cmd_use_project(args):
    """Switch to a different project."""
    set_current_project(args.project_id)
    print(f"✓ Switched to project: {args.project_id}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Context Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # log-decision command
    p_decision = subparsers.add_parser('log-decision', help='Log a development decision')
    p_decision.add_argument('decision', help='The decision made')
    p_decision.add_argument('reasoning', help='Why this decision was made')
    p_decision.set_defaults(func=cmd_log_decision)
    
    # log-error command
    p_error = subparsers.add_parser('log-error', help='Log an error')
    p_error.add_argument('error', help='Error message')
    p_error.add_argument('--context', help='Additional context (JSON string)')
    p_error.set_defaults(func=cmd_log_error)
    
    # suggest command
    p_suggest = subparsers.add_parser('suggest', help='Get task suggestions')
    p_suggest.set_defaults(func=cmd_suggest)
    
    # stats command
    p_stats = subparsers.add_parser('stats', help='Show statistics')
    p_stats.set_defaults(func=cmd_stats)
    
    # query command
    p_query = subparsers.add_parser('query', help='Query contexts')
    p_query.add_argument('query', nargs='*', help='Search text')
    p_query.add_argument('--type', help='Filter by context type')
    p_query.add_argument('--since', type=int, help='Hours ago to search from')
    p_query.add_argument('--limit', type=int, default=10, help='Max results')
    p_query.set_defaults(func=cmd_query)
    
    # list-projects command
    p_list = subparsers.add_parser('list-projects', help='List all projects')
    p_list.set_defaults(func=cmd_list_projects)
    
    # use-project command
    p_use = subparsers.add_parser('use-project', help='Switch to a project')
    p_use.add_argument('project_id', help='Project ID to switch to')
    p_use.set_defaults(func=cmd_use_project)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()