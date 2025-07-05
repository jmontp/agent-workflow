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
    cm = ContextManager()
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
    cm = ContextManager()
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
    cm = ContextManager()
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
    cm = ContextManager()
    stats = cm.get_stats()
    
    print(f"📊 Context Manager Statistics")
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
    cm = ContextManager()
    
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


def cmd_analyze_doc(args):
    """Analyze a documentation file."""
    cm = ContextManager()
    
    try:
        metadata = cm.analyze_doc(args.doc_path)
        print(f"📄 Analyzed: {args.doc_path}")
        print(f"   Type: {metadata.doc_type}")
        print(f"   Quality scores:")
        for metric, score in metadata.quality_scores.items():
            print(f"     - {metric}: {score:.2f}")
        
        if metadata.staleness_indicators:
            print(f"   ⚠️  Staleness indicators: {', '.join(metadata.staleness_indicators)}")
    except Exception as e:
        print(f"❌ Error: {e}")


def cmd_learn_patterns(args):
    """Learn documentation patterns."""
    cm = ContextManager()
    
    print("🔍 Learning documentation patterns...")
    patterns = cm.learn_doc_patterns(args.paths if args.paths else None)
    
    print(f"\n📊 Patterns learned:")
    print(f"   Unique headers: {len(patterns.section_headers)}")
    print(f"   Common phrases: {len(patterns.common_phrases)}")
    print(f"   Markdown style: {patterns.markdown_style}")
    print(f"   List style: '{patterns.list_style}'")
    
    if patterns.common_phrases:
        print(f"\n   Top phrases:")
        sorted_phrases = sorted(patterns.common_phrases.items(), key=lambda x: x[1], reverse=True)[:5]
        for phrase, count in sorted_phrases:
            print(f"     - '{phrase}': {count} occurrences")


def cmd_doc_quality(args):
    """Check documentation quality."""
    cm = ContextManager()
    
    scores = cm.calculate_doc_quality(args.doc_path)
    
    print(f"📊 Quality scores for {args.doc_path}:")
    overall = 0
    for metric, score in scores.items():
        print(f"   {metric}: {'█' * int(score * 10)}{'░' * (10 - int(score * 10))} {score:.2f}")
        if metric != 'error':
            overall += score
    
    if 'error' not in scores:
        overall_avg = overall / len(scores)
        print(f"\n   Overall: {'█' * int(overall_avg * 10)}{'░' * (10 - int(overall_avg * 10))} {overall_avg:.2f}")


def cmd_init(args):
    """Initialize project by scanning all files."""
    cm = ContextManager()
    
    print("🔍 Initializing project...")
    print(f"   Root: {args.path}\n")
    
    result = cm.initialize_project(args.path)
    
    if result['success']:
        print("✅ Project initialized successfully!\n")
        print(f"📊 Summary:")
        print(f"   Files scanned: {result['files_scanned']}")
        print(f"   Documentation: {result['docs_scanned']} files")
        print(f"   Code files: {result['code_scanned']} files")
        print(f"   Concepts mapped: {result['concepts_mapped']}")
        print(f"   Relationships: {result['relationships']}")
        print(f"   Duration: {result['duration_seconds']:.2f} seconds")
        print(f"\n💡 You can now use 'cm find' to search for information")
    else:
        print("❌ Failed to initialize project")


def cmd_find(args):
    """Find information in the project."""
    cm = ContextManager()
    
    query = ' '.join(args.query)
    print(f"🔍 Searching for: {query}\n")
    
    try:
        results = cm.find_information(query)
        
        if not results:
            print("No results found.")
        else:
            print(f"Found {len(results)} locations:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.file}")
                print(f"   Type: {result.content}")
                print(f"   Context: {result.context}")
                print(f"   Confidence: {result.confidence:.1%}\n")
    except ValueError as e:
        print(f"❌ {e}")
        print("   Run 'cm init' first to scan the project")


def cmd_status(args):
    """Show project initialization status."""
    cm = ContextManager()
    status = cm.get_project_status()
    
    print(f"📊 Project Status\n")
    
    if status['initialized']:
        print("✅ Project is initialized")
        print(f"   Last indexed: {status['index_timestamp']}")
        print(f"   Total concepts: {status['total_concepts']}")
        print(f"   Total functions: {status['total_functions']}")
        print(f"   Total classes: {status['total_classes']}")
        print(f"   Documentation files: {status.get('total_docs', 'N/A')}")
        print(f"   Code files: {status.get('total_code_files', 'N/A')}")
    else:
        print("❌ " + status['message'])


def cmd_explain(args):
    """Explain a concept or answer a question using AI."""
    cm = ContextManager()
    
    query = ' '.join(args.query)
    print(f"🤖 Explaining: {query}\n")
    
    # First show deterministic results
    print("📍 Quick lookup results:\n")
    cmd_find_args = type('obj', (object,), {'query': args.query})
    cmd_find(cmd_find_args)
    
    # Then add AI explanation if requested
    if args.ai:
        print("\n🧠 AI-Enhanced Explanation:\n")
        try:
            explanation = cm.explain_with_ai(query)
            print(explanation)
        except ImportError:
            print("❌ AI tools not available. Add claude_tools.py to aw_docs/")
        except Exception as e:
            print(f"❌ Error: {e}")


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
    
    # analyze-doc command
    p_analyze = subparsers.add_parser('analyze-doc', help='Analyze a documentation file')
    p_analyze.add_argument('doc_path', help='Path to markdown file')
    p_analyze.set_defaults(func=cmd_analyze_doc)
    
    # learn-patterns command
    p_learn = subparsers.add_parser('learn-patterns', help='Learn documentation patterns')
    p_learn.add_argument('paths', nargs='*', help='Specific doc paths (optional)')
    p_learn.set_defaults(func=cmd_learn_patterns)
    
    # doc-quality command
    p_quality = subparsers.add_parser('doc-quality', help='Check documentation quality')
    p_quality.add_argument('doc_path', help='Path to markdown file')
    p_quality.set_defaults(func=cmd_doc_quality)
    
    # init command
    p_init = subparsers.add_parser('init', help='Initialize project by scanning all files')
    p_init.add_argument('path', nargs='?', default='.', help='Project root path (default: current directory)')
    p_init.set_defaults(func=cmd_init)
    
    # find command
    p_find = subparsers.add_parser('find', help='Find information in the project')
    p_find.add_argument('query', nargs='+', help='Search query')
    p_find.set_defaults(func=cmd_find)
    
    # status command
    p_status = subparsers.add_parser('status', help='Show project initialization status')
    p_status.set_defaults(func=cmd_status)
    
    # explain command
    p_explain = subparsers.add_parser('explain', help='Explain a concept or answer a question')
    p_explain.add_argument('query', nargs='+', help='What to explain')
    p_explain.add_argument('--ai', action='store_true', help='Include AI-enhanced explanation')
    p_explain.set_defaults(func=cmd_explain)
    
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