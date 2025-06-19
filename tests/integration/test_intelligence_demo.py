#!/usr/bin/env python3
"""
Context Intelligence Layer Demonstration

This script demonstrates the intelligent context filtering, compression,
and indexing capabilities of the Context Management System.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from context_manager import ContextManager
from context.models import ContextRequest, CompressionLevel, FileType
from tdd_models import TDDState


async def demo_context_intelligence():
    """Demonstrate the context intelligence layer functionality"""
    
    print("=" * 80)
    print("Context Intelligence Layer Demonstration")
    print("=" * 80)
    
    # Initialize ContextManager with intelligence enabled
    print("\n1. Initializing ContextManager with intelligence layer...")
    context_manager = ContextManager(
        project_path=".",  # Use current project
        enable_intelligence=True,
        max_tokens=50000
    )
    
    # Build the context index
    print("2. Building context index...")
    try:
        await context_manager.build_context_index(force_rebuild=True)
        print("   ✓ Context index built successfully")
    except Exception as e:
        print(f"   ✗ Error building index: {str(e)}")
        return
    
    # Demonstrate codebase search
    print("\n3. Demonstrating codebase search...")
    search_queries = ["ContextManager", "filter", "compression", "test"]
    
    for query in search_queries:
        try:
            results = await context_manager.search_codebase(
                query=query,
                search_type="all",
                max_results=5
            )
            
            print(f"\n   Search results for '{query}':")
            for i, result in enumerate(results[:3], 1):
                print(f"      {i}. {Path(result['file_path']).name} (score: {result['relevance_score']:.3f})")
                print(f"         Match: {result['match_type']} - {', '.join(result['matches'][:2])}")
        
        except Exception as e:
            print(f"   ✗ Error searching for '{query}': {str(e)}")
    
    # Demonstrate dependency analysis
    print("\n4. Analyzing file dependencies...")
    try:
        # Find a Python file to analyze
        python_files = list(Path(".").rglob("*.py"))
        if python_files:
            sample_file = str(python_files[0])
            deps = await context_manager.get_file_dependencies(
                file_path=sample_file,
                depth=1,
                include_reverse=True
            )
            
            print(f"   Dependencies for {Path(sample_file).name}:")
            print(f"      Direct dependencies: {deps.get('dependency_count', 0)}")
            print(f"      Reverse dependencies: {deps.get('reverse_dependency_count', 0)}")
            
            if deps.get('direct_dependencies'):
                print(f"      Imports: {', '.join(deps['direct_dependencies'][:3])}")
        
    except Exception as e:
        print(f"   ✗ Error analyzing dependencies: {str(e)}")
    
    # Demonstrate intelligent context preparation
    print("\n5. Preparing intelligent context...")
    try:
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task={
                "description": "Implement context filtering with relevance scoring algorithm",
                "acceptance_criteria": "Filter files by relevance using multi-factor scoring",
                "current_state": TDDState.GREEN.value
            },
            story_id="context-intelligence-demo",
            max_tokens=20000,
            compression_level=CompressionLevel.MODERATE,
            focus_areas=["context", "filtering", "scoring"]
        )
        
        print(f"   ✓ Context prepared successfully")
        print(f"      Agent: {context.agent_type}")
        print(f"      Story: {context.story_id}")
        print(f"      Files included: {len(context.file_contents)}")
        print(f"      Token usage: {context.token_usage.total_used if context.token_usage else 'N/A'}")
        print(f"      Compression applied: {context.compression_applied}")
        
        if context.relevance_scores:
            print(f"      Top relevant files:")
            for i, score in enumerate(context.relevance_scores[:3], 1):
                print(f"         {i}. {Path(score.file_path).name} (score: {score.total_score:.3f})")
                if score.reasons:
                    print(f"            Reasons: {', '.join(score.reasons[:2])}")
    
    except Exception as e:
        print(f"   ✗ Error preparing context: {str(e)}")
    
    # Demonstrate compression analysis
    print("\n6. Analyzing compression potential...")
    try:
        # Read a sample Python file
        python_files = list(Path("lib").rglob("*.py"))
        if python_files:
            sample_file = python_files[0]
            content = sample_file.read_text(encoding='utf-8', errors='ignore')
            
            analysis = await context_manager.estimate_compression_potential(
                content=content,
                file_type=FileType.PYTHON,
                compression_level=CompressionLevel.MODERATE
            )
            
            print(f"   Compression analysis for {sample_file.name}:")
            print(f"      Original tokens: {analysis.get('original_tokens', 'N/A')}")
            print(f"      Estimated compression ratio: {analysis.get('estimated_compression_ratio', 'N/A'):.3f}")
            print(f"      Estimated final tokens: {analysis.get('estimated_final_tokens', 'N/A')}")
            
            if analysis.get('compressible_elements'):
                print(f"      Compressible elements: {', '.join(analysis['compressible_elements'][:3])}")
    
    except Exception as e:
        print(f"   ✗ Error analyzing compression: {str(e)}")
    
    # Demonstrate project statistics
    print("\n7. Generating project statistics...")
    try:
        stats = await context_manager.get_project_statistics()
        
        print(f"   Project overview:")
        print(f"      Total files: {stats.get('total_files', 'N/A')}")
        print(f"      Total dependencies: {stats.get('total_dependencies', 'N/A')}")
        
        if stats.get('file_types'):
            print(f"      File types: {dict(list(stats['file_types'].items())[:3])}")
        
        if stats.get('most_depended_upon_files'):
            print(f"      Most depended upon files:")
            for file_path, count in stats['most_depended_upon_files'][:3]:
                print(f"         {Path(file_path).name}: {count} dependencies")
    
    except Exception as e:
        print(f"   ✗ Error generating statistics: {str(e)}")
    
    # Show performance metrics
    print("\n8. Performance metrics...")
    try:
        metrics = context_manager.get_performance_metrics()
        
        cm_metrics = metrics.get('context_manager', {})
        print(f"   Context Manager performance:")
        print(f"      Total requests: {cm_metrics.get('total_requests', 'N/A')}")
        print(f"      Cache hit rate: {cm_metrics.get('cache_hit_rate', 'N/A'):.3f}")
        print(f"      Average preparation time: {cm_metrics.get('average_preparation_time', 'N/A'):.3f}s")
        print(f"      Active contexts: {cm_metrics.get('active_contexts', 'N/A')}")
    
    except Exception as e:
        print(f"   ✗ Error getting performance metrics: {str(e)}")
    
    # Clean up
    print("\n9. Cleaning up...")
    try:
        if hasattr(context_manager, 'context_index') and context_manager.context_index:
            await context_manager.context_index.close()
        print("   ✓ Cleanup completed")
    except Exception as e:
        print(f"   ✗ Error during cleanup: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Context Intelligence Layer demonstration completed!")
    print("=" * 80)


async def demo_filtering_algorithm():
    """Demonstrate the multi-factor relevance scoring algorithm"""
    
    print("\n" + "=" * 80)
    print("Multi-Factor Relevance Scoring Algorithm Demo")
    print("=" * 80)
    
    # Create a mock context request
    request = ContextRequest(
        agent_type="CodeAgent",
        story_id="scoring-demo",
        task={
            "description": "Implement context filtering with multi-factor relevance scoring",
            "acceptance_criteria": "Use 40% direct mention + 25% dependency + 20% historical + 10% semantic + 5% TDD phase"
        },
        max_tokens=30000,
        focus_areas=["context", "filtering", "relevance", "scoring"]
    )
    
    print(f"\nTask: {request.task['description']}")
    print(f"Agent: {request.agent_type}")
    print(f"Focus areas: {', '.join(request.focus_areas)}")
    
    # Initialize context manager
    context_manager = ContextManager(
        project_path=".",
        enable_intelligence=True
    )
    
    try:
        await context_manager.build_context_index()
        
        # Find relevant files
        candidate_files = []
        for py_file in Path(".").rglob("*.py"):
            if "lib" in str(py_file) or "test" in str(py_file):
                candidate_files.append(str(py_file))
        
        if candidate_files:
            print(f"\nAnalyzing {len(candidate_files)} candidate files...")
            
            # Get relevance scores
            relevance_scores = await context_manager.context_filter.filter_relevant_files(
                request=request,
                candidate_files=candidate_files[:10],  # Limit for demo
                max_files=5,
                min_score_threshold=0.05
            )
            
            print(f"\nTop {len(relevance_scores)} relevant files:")
            print("File".ljust(25) + "Score".ljust(8) + "Direct".ljust(8) + "Deps".ljust(8) + "Hist".ljust(8) + "Sem".ljust(8) + "TDD".ljust(8) + "Reasons")
            print("-" * 80)
            
            for score in relevance_scores:
                file_name = Path(score.file_path).name[:24]
                reasons_str = ', '.join(score.reasons[:2]) if score.reasons else ""
                reasons_str = reasons_str[:30] + "..." if len(reasons_str) > 30 else reasons_str
                
                print(
                    f"{file_name:<25}"
                    f"{score.total_score:<8.3f}"
                    f"{score.direct_mention:<8.3f}"
                    f"{score.dependency_score:<8.3f}"
                    f"{score.historical_score:<8.3f}"
                    f"{score.semantic_score:<8.3f}"
                    f"{score.tdd_phase_score:<8.3f}"
                    f"{reasons_str}"
                )
            
            # Show detailed explanation for top file
            if relevance_scores:
                print(f"\nDetailed analysis for top file: {Path(relevance_scores[0].file_path).name}")
                explanation = await context_manager.get_file_relevance_explanation(
                    file_path=relevance_scores[0].file_path,
                    request=request
                )
                
                breakdown = explanation.get('scoring_breakdown', {})
                for component, details in breakdown.items():
                    contribution = details.get('contribution', 0)
                    weight = details.get('weight', 0)
                    score = details.get('score', 0)
                    print(f"  {component.replace('_', ' ').title()}: {score:.3f} × {weight:.1%} = {contribution:.3f}")
        
        # Close the index
        if hasattr(context_manager, 'context_index') and context_manager.context_index:
            await context_manager.context_index.close()
    
    except Exception as e:
        print(f"Error in filtering demo: {str(e)}")


if __name__ == "__main__":
    print("Starting Context Intelligence Layer Demonstration...")
    
    try:
        # Run the main demonstration
        asyncio.run(demo_context_intelligence())
        
        # Run the filtering algorithm demo
        asyncio.run(demo_filtering_algorithm())
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\nDemo completed!")