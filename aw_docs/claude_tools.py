#!/usr/bin/env python3
"""
Claude Tools - AI-powered enhancements for Context Manager.
Provides optional AI capabilities while keeping the core deterministic.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class ClaudeTools:
    """AI-powered tools for Context Manager enhancement."""
    
    def __init__(self, context_manager):
        """Initialize with a Context Manager instance."""
        self.cm = context_manager
    
    def explain_with_context(self, query: str) -> str:
        """
        Use project context for AI-powered explanations.
        Combines deterministic search with AI understanding.
        
        Args:
            query: Natural language question
            
        Returns:
            AI-generated explanation with project context
        """
        # First, use deterministic search
        locations = self.cm.find_information(query)
        contexts = self.cm.query_contexts(query=query, limit=5)
        
        # Build context for AI
        context_data = {
            "query": query,
            "found_locations": [
                {
                    "file": loc.file,
                    "content": loc.content,
                    "context": loc.context
                }
                for loc in locations[:5]
            ],
            "related_contexts": [
                {
                    "type": ctx.type.value,
                    "data": ctx.data,
                    "timestamp": ctx.timestamp.isoformat()
                }
                for ctx in contexts
            ]
        }
        
        # TODO: Call Claude API with context
        # For now, return structured summary
        return self._format_explanation(query, locations, contexts)
    
    def generate_documentation(self, file_path: str) -> str:
        """
        Generate documentation for a code file using AI.
        
        Args:
            file_path: Path to code file
            
        Returns:
            Generated documentation in markdown
        """
        # Get code metadata
        code_meta = self.cm.project_index.code_files.get(file_path)
        if not code_meta:
            return f"File {file_path} not found in project index"
        
        # Build context
        context = {
            "file": file_path,
            "language": code_meta.language,
            "functions": code_meta.functions,
            "classes": code_meta.classes,
            "imports": code_meta.imports,
            "lines_of_code": code_meta.lines_of_code
        }
        
        # TODO: Call Claude API to generate docs
        # For now, return template
        return self._generate_doc_template(code_meta)
    
    def suggest_refactoring(self, file_path: str) -> List[Dict[str, str]]:
        """
        Suggest refactoring improvements for a file.
        
        Args:
            file_path: Path to analyze
            
        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        
        # Get file metadata
        code_meta = self.cm.project_index.code_files.get(file_path)
        if not code_meta:
            return suggestions
        
        # Analyze patterns
        if code_meta.complexity_score > 0.7:
            suggestions.append({
                "type": "complexity",
                "suggestion": "Consider breaking down complex functions",
                "reason": f"Complexity score: {code_meta.complexity_score:.2f}"
            })
        
        if len(code_meta.functions) > 20:
            suggestions.append({
                "type": "size",
                "suggestion": "Consider splitting into multiple modules",
                "reason": f"File contains {len(code_meta.functions)} functions"
            })
        
        # TODO: Deep AI analysis with Claude
        return suggestions
    
    def analyze_patterns_deep(self) -> Dict[str, Any]:
        """
        Deep pattern analysis using AI to find non-obvious patterns.
        
        Returns:
            Dictionary of discovered patterns and insights
        """
        # Gather all contexts and patterns
        all_contexts = list(self.cm.contexts.values())
        patterns = self.cm.get_patterns()
        
        # Group by type and time
        insights = {
            "decision_patterns": self._analyze_decisions(all_contexts),
            "error_patterns": self._analyze_errors(all_contexts),
            "workflow_patterns": self._analyze_workflow(all_contexts),
            "suggestions": []
        }
        
        # TODO: Send to Claude for deep analysis
        return insights
    
    def explain_concept(self, concept: str) -> str:
        """
        Explain a concept using project context and AI understanding.
        
        Args:
            concept: Concept to explain
            
        Returns:
            AI-generated explanation
        """
        # Find all occurrences
        locations = self.cm.project_index.concepts.get(concept, [])
        
        if not locations:
            return f"Concept '{concept}' not found in project"
        
        # Build context from all mentions
        context_snippets = []
        for loc in locations[:10]:  # Limit to 10 files
            try:
                content = Path(loc).read_text()
                # Extract surrounding context
                # TODO: Smart context extraction
                context_snippets.append({
                    "file": loc,
                    "mentions": content.count(concept)
                })
            except:
                pass
        
        # TODO: Call Claude for explanation
        return self._format_concept_explanation(concept, context_snippets)
    
    # Helper methods
    def _format_explanation(self, query: str, locations: List, contexts: List) -> str:
        """Format explanation from search results."""
        explanation = f"# Query: {query}\n\n"
        
        if locations:
            explanation += "## Found in:\n"
            for loc in locations[:5]:
                explanation += f"- **{loc.file}** ({loc.confidence:.0%} confidence)\n"
                explanation += f"  - {loc.context}\n"
        
        if contexts:
            explanation += "\n## Related Contexts:\n"
            for ctx in contexts[:3]:
                explanation += f"- **{ctx.type.value}** ({ctx.timestamp.strftime('%Y-%m-%d')})\n"
                if ctx.type.value == "decision":
                    explanation += f"  - Decision: {ctx.data.get('decision', 'N/A')}\n"
                elif ctx.type.value == "error":
                    explanation += f"  - Error: {ctx.data.get('error', 'N/A')}\n"
        
        return explanation
    
    def _generate_doc_template(self, code_meta) -> str:
        """Generate basic documentation template."""
        doc = f"# {Path(code_meta.path).name}\n\n"
        doc += f"**Language**: {code_meta.language}\n"
        doc += f"**Lines of Code**: {code_meta.lines_of_code}\n\n"
        
        if code_meta.classes:
            doc += "## Classes\n\n"
            for cls in code_meta.classes:
                doc += f"### {cls}\n\n"
                if cls in code_meta.docstrings:
                    doc += f"{code_meta.docstrings[cls]}\n\n"
                else:
                    doc += "TODO: Add class description\n\n"
        
        if code_meta.functions:
            doc += "## Functions\n\n"
            for func in code_meta.functions:
                doc += f"### {func}\n\n"
                if func in code_meta.docstrings:
                    doc += f"{code_meta.docstrings[func]}\n\n"
                else:
                    doc += "TODO: Add function description\n\n"
        
        return doc
    
    def _format_concept_explanation(self, concept: str, snippets: List) -> str:
        """Format concept explanation."""
        explanation = f"# Concept: {concept}\n\n"
        explanation += f"Found in {len(snippets)} files across the project.\n\n"
        
        total_mentions = sum(s['mentions'] for s in snippets)
        explanation += f"Total mentions: {total_mentions}\n\n"
        
        explanation += "## Occurrences:\n"
        for snippet in snippets[:5]:
            explanation += f"- {snippet['file']} ({snippet['mentions']} mentions)\n"
        
        return explanation
    
    def _analyze_decisions(self, contexts: List) -> Dict:
        """Analyze decision patterns."""
        decisions = [c for c in contexts if c.type.value == "decision"]
        return {
            "total": len(decisions),
            "recent_count": len([d for d in decisions if "architecture" in str(d.data).lower()]),
            "common_keywords": self._extract_keywords([d.data.get('decision', '') for d in decisions])
        }
    
    def _analyze_errors(self, contexts: List) -> Dict:
        """Analyze error patterns."""
        errors = [c for c in contexts if c.type.value == "error"]
        return {
            "total": len(errors),
            "types": self._count_error_types(errors)
        }
    
    def _analyze_workflow(self, contexts: List) -> Dict:
        """Analyze workflow patterns."""
        # Group contexts by hour to find patterns
        by_hour = {}
        for ctx in contexts:
            hour = ctx.timestamp.hour
            by_hour[hour] = by_hour.get(hour, 0) + 1
        
        return {
            "most_active_hours": sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:3],
            "total_contexts": len(contexts)
        }
    
    def _extract_keywords(self, texts: List[str], top_n: int = 10) -> List[str]:
        """Extract common keywords from texts."""
        word_counts = {}
        for text in texts:
            words = text.lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def _count_error_types(self, errors: List) -> Dict[str, int]:
        """Count error types."""
        types = {}
        for error in errors:
            error_str = str(error.data.get('error', 'unknown'))
            # Simple classification
            if 'file' in error_str.lower():
                types['file_errors'] = types.get('file_errors', 0) + 1
            elif 'type' in error_str.lower():
                types['type_errors'] = types.get('type_errors', 0) + 1
            else:
                types['other'] = types.get('other', 0) + 1
        
        return types