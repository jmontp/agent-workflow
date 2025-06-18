"""
Context Filter - Intelligent Context Filtering System

Multi-factor relevance scoring for selecting the most relevant files and content
for agent context. Implements sophisticated filtering algorithms based on:
- Direct mention analysis (40% weight)
- Dependency analysis (25% weight) 
- Historical access patterns (20% weight)
- Semantic similarity (10% weight)
- TDD phase relevance (5% weight)
"""

import asyncio
import logging
import re
import ast
import json
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta

try:
    from .context.models import (
        RelevanceScore, 
        FileType, 
        ContextRequest, 
        AgentContext,
        CompressionLevel
    )
    from .tdd_models import TDDState
    from .agent_memory import FileBasedAgentMemory
    from .token_calculator import TokenCalculator
except ImportError:
    from context.models import (
        RelevanceScore, 
        FileType, 
        ContextRequest, 
        AgentContext,
        CompressionLevel
    )
    from tdd_models import TDDState
    from agent_memory import FileBasedAgentMemory
    from token_calculator import TokenCalculator

logger = logging.getLogger(__name__)


class ContextFilter:
    """
    Intelligent context filtering with multi-factor relevance scoring.
    
    Implements a sophisticated relevance algorithm combining:
    - Direct mention score (40%): Keywords, function names, class names in task
    - Dependency score (25%): Import relationships and file dependencies
    - Historical score (20%): Past access patterns and agent preferences
    - Semantic score (10%): Content similarity and conceptual relevance  
    - TDD phase score (5%): Relevance to current TDD cycle phase
    """
    
    # Scoring weights for relevance algorithm
    DIRECT_MENTION_WEIGHT = 0.40
    DEPENDENCY_WEIGHT = 0.25
    HISTORICAL_WEIGHT = 0.20
    SEMANTIC_WEIGHT = 0.10
    TDD_PHASE_WEIGHT = 0.05
    
    def __init__(
        self,
        project_path: str,
        agent_memory: Optional[FileBasedAgentMemory] = None,
        token_calculator: Optional[TokenCalculator] = None
    ):
        """
        Initialize ContextFilter.
        
        Args:
            project_path: Path to project root
            agent_memory: Agent memory for historical patterns
            token_calculator: Token calculator for content sizing
        """
        self.project_path = Path(project_path)
        self.agent_memory = agent_memory
        self.token_calculator = token_calculator or TokenCalculator()
        
        # Caching for performance
        self._file_dependencies_cache: Dict[str, Set[str]] = {}
        self._file_type_cache: Dict[str, FileType] = {}
        self._content_cache: Dict[str, str] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Performance metrics
        self._filtering_times: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(f"ContextFilter initialized for project: {self.project_path}")
    
    async def filter_relevant_files(
        self,
        request: ContextRequest,
        candidate_files: List[str],
        max_files: int = 20,
        min_score_threshold: float = 0.1
    ) -> List[RelevanceScore]:
        """
        Filter and score files for relevance to the request.
        
        Args:
            request: Context request with task details
            candidate_files: List of candidate file paths
            max_files: Maximum number of files to return
            min_score_threshold: Minimum relevance score to include
            
        Returns:
            List of RelevanceScore objects sorted by relevance
        """
        start_time = datetime.now()
        
        try:
            # Extract search terms from request
            search_terms = await self._extract_search_terms(request)
            
            # Calculate relevance scores for each file
            scored_files = []
            for file_path in candidate_files:
                try:
                    score = await self._calculate_relevance_score(
                        file_path, request, search_terms
                    )
                    
                    if score.total_score >= min_score_threshold:
                        scored_files.append(score)
                        
                except Exception as e:
                    logger.warning(f"Error scoring file {file_path}: {str(e)}")
                    continue
            
            # Sort by total score (descending) and limit results
            scored_files.sort(key=lambda x: x.total_score, reverse=True)
            result = scored_files[:max_files]
            
            # Track performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self._filtering_times.append(elapsed)
            
            logger.info(
                f"Filtered {len(candidate_files)} files to {len(result)} relevant files "
                f"in {elapsed:.3f}s (avg score: {sum(s.total_score for s in result) / len(result) if result else 0:.3f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in file filtering: {str(e)}")
            return []
    
    async def filter_content_by_relevance(
        self,
        file_path: str,
        content: str,
        request: ContextRequest,
        target_tokens: int
    ) -> str:
        """
        Filter content within a file to extract most relevant sections.
        
        Args:
            file_path: Path to the file
            content: File content to filter
            request: Context request
            target_tokens: Target token count for filtered content
            
        Returns:
            Filtered content preserving most relevant sections
        """
        file_type = await self._get_file_type(file_path)
        
        if file_type == FileType.PYTHON:
            return await self._filter_python_content(content, request, target_tokens)
        elif file_type in [FileType.MARKDOWN, FileType.CONFIG]:
            return await self._filter_text_content(content, request, target_tokens)
        elif file_type == FileType.TEST:
            return await self._filter_test_content(content, request, target_tokens)
        else:
            # For other file types, use simple truncation
            return await self._truncate_content(content, target_tokens)
    
    async def get_file_relevance_explanation(
        self,
        file_path: str,
        request: ContextRequest
    ) -> Dict[str, Any]:
        """
        Get detailed explanation of why a file is relevant.
        
        Args:
            file_path: Path to the file
            request: Context request
            
        Returns:
            Dictionary with detailed relevance breakdown
        """
        search_terms = await self._extract_search_terms(request)
        score = await self._calculate_relevance_score(file_path, request, search_terms)
        
        return {
            "file_path": file_path,
            "total_score": score.total_score,
            "scoring_breakdown": {
                "direct_mention": {
                    "score": score.direct_mention,
                    "weight": self.DIRECT_MENTION_WEIGHT,
                    "contribution": score.direct_mention * self.DIRECT_MENTION_WEIGHT
                },
                "dependency": {
                    "score": score.dependency_score,
                    "weight": self.DEPENDENCY_WEIGHT,
                    "contribution": score.dependency_score * self.DEPENDENCY_WEIGHT
                },
                "historical": {
                    "score": score.historical_score,
                    "weight": self.HISTORICAL_WEIGHT,
                    "contribution": score.historical_score * self.HISTORICAL_WEIGHT
                },
                "semantic": {
                    "score": score.semantic_score,
                    "weight": self.SEMANTIC_WEIGHT,
                    "contribution": score.semantic_score * self.SEMANTIC_WEIGHT
                },
                "tdd_phase": {
                    "score": score.tdd_phase_score,
                    "weight": self.TDD_PHASE_WEIGHT,
                    "contribution": score.tdd_phase_score * self.TDD_PHASE_WEIGHT
                }
            },
            "reasons": score.reasons,
            "search_terms": search_terms
        }
    
    # Private implementation methods
    
    async def _extract_search_terms(self, request: ContextRequest) -> Dict[str, List[str]]:
        """Extract search terms from context request"""
        search_terms = {
            "keywords": [],
            "function_names": [],
            "class_names": [],
            "file_patterns": [],
            "concepts": []
        }
        
        # Extract from task description
        task_text = ""
        if request.task:
            if hasattr(request.task, 'description'):
                task_text = request.task.description
            elif isinstance(request.task, dict):
                task_text = request.task.get('description', '')
                task_text += " " + request.task.get('acceptance_criteria', '')
        
        # Extract from focus areas
        for focus_area in request.focus_areas:
            task_text += " " + focus_area
        
        if not task_text:
            return search_terms
        
        # Extract function/method names (snake_case and camelCase)
        function_pattern = r'(?:def\s+|function\s+|method\s+)?([a-z_][a-zA-Z0-9_]*)\s*\('
        search_terms["function_names"] = list(set(re.findall(function_pattern, task_text, re.IGNORECASE)))
        
        # Extract class names (PascalCase)
        class_pattern = r'(?:class\s+)?([A-Z][a-zA-Z0-9_]*)'
        search_terms["class_names"] = list(set(re.findall(class_pattern, task_text)))
        
        # Extract file patterns
        file_pattern = r'([a-zA-Z0-9_.-]+\.[a-zA-Z]{2,4})'
        search_terms["file_patterns"] = list(set(re.findall(file_pattern, task_text)))
        
        # Extract general keywords (filter out common words)
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'a', 'an'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', task_text.lower())
        search_terms["keywords"] = [w for w in set(words) if w not in common_words][:20]
        
        # Extract programming concepts
        programming_concepts = [
            'test', 'testing', 'unittest', 'pytest', 'mock', 'fixture',
            'api', 'endpoint', 'route', 'controller', 'service', 'model',
            'database', 'migration', 'schema', 'query', 'index',
            'authentication', 'authorization', 'security', 'validation',
            'configuration', 'settings', 'environment', 'deployment',
            'logging', 'monitoring', 'performance', 'optimization',
            'integration', 'component', 'module', 'package', 'import'
        ]
        
        found_concepts = [concept for concept in programming_concepts 
                         if concept in task_text.lower()]
        search_terms["concepts"] = found_concepts
        
        return search_terms
    
    async def _calculate_relevance_score(
        self,
        file_path: str,
        request: ContextRequest,
        search_terms: Dict[str, List[str]]
    ) -> RelevanceScore:
        """Calculate comprehensive relevance score for a file"""
        
        # Initialize score components
        direct_mention = 0.0
        dependency_score = 0.0
        historical_score = 0.0
        semantic_score = 0.0
        tdd_phase_score = 0.0
        reasons = []
        
        try:
            # Get file content for analysis
            content = await self._get_file_content(file_path)
            file_type = await self._get_file_type(file_path)
            
            # 1. Direct mention score (40% weight)
            direct_mention = await self._calculate_direct_mention_score(
                content, search_terms, file_path
            )
            if direct_mention > 0.3:
                reasons.append(f"High direct mention score ({direct_mention:.2f})")
            
            # 2. Dependency score (25% weight)
            dependency_score = await self._calculate_dependency_score(
                file_path, search_terms, request
            )
            if dependency_score > 0.3:
                reasons.append(f"Strong dependency relationships ({dependency_score:.2f})")
            
            # 3. Historical score (20% weight)
            if self.agent_memory:
                historical_score = await self._calculate_historical_score(
                    file_path, request.agent_type, request.story_id
                )
                if historical_score > 0.3:
                    reasons.append(f"Frequently accessed file ({historical_score:.2f})")
            
            # 4. Semantic score (10% weight)
            semantic_score = await self._calculate_semantic_score(
                content, file_type, request
            )
            if semantic_score > 0.3:
                reasons.append(f"High semantic relevance ({semantic_score:.2f})")
            
            # 5. TDD phase score (5% weight)
            if request.task and hasattr(request.task, 'current_state'):
                tdd_phase_score = await self._calculate_tdd_phase_score(
                    file_path, file_type, request.task.current_state
                )
                if tdd_phase_score > 0.3:
                    reasons.append(f"Relevant to TDD phase ({tdd_phase_score:.2f})")
            
            # Calculate weighted total score
            total_score = (
                direct_mention * self.DIRECT_MENTION_WEIGHT +
                dependency_score * self.DEPENDENCY_WEIGHT +
                historical_score * self.HISTORICAL_WEIGHT +
                semantic_score * self.SEMANTIC_WEIGHT +
                tdd_phase_score * self.TDD_PHASE_WEIGHT
            )
            
            return RelevanceScore(
                file_path=file_path,
                total_score=total_score,
                direct_mention=direct_mention,
                dependency_score=dependency_score,
                historical_score=historical_score,
                semantic_score=semantic_score,
                tdd_phase_score=tdd_phase_score,
                reasons=reasons
            )
            
        except Exception as e:
            logger.warning(f"Error calculating relevance for {file_path}: {str(e)}")
            return RelevanceScore(
                file_path=file_path,
                total_score=0.0,
                reasons=[f"Error in analysis: {str(e)}"]
            )
    
    async def _calculate_direct_mention_score(
        self,
        content: str,
        search_terms: Dict[str, List[str]],
        file_path: str
    ) -> float:
        """Calculate direct mention score based on keyword presence"""
        if not content:
            return 0.0
        
        content_lower = content.lower()
        file_name = Path(file_path).name.lower()
        
        # Score components
        keyword_score = 0.0
        function_score = 0.0
        class_score = 0.0
        filename_score = 0.0
        
        # Keyword matches (weighted by frequency)
        for keyword in search_terms.get("keywords", []):
            count = content_lower.count(keyword.lower())
            if count > 0:
                keyword_score += min(count * 0.1, 0.5)  # Cap at 0.5 per keyword
        
        # Function name matches (higher weight)
        for func_name in search_terms.get("function_names", []):
            if func_name.lower() in content_lower:
                function_score += 0.3
                # Extra points for function definitions
                if f"def {func_name}" in content_lower:
                    function_score += 0.2
        
        # Class name matches (highest weight)
        for class_name in search_terms.get("class_names", []):
            if class_name.lower() in content_lower:
                class_score += 0.4
                # Extra points for class definitions
                if f"class {class_name}" in content_lower:
                    class_score += 0.3
        
        # Filename relevance
        for term in search_terms.get("keywords", []) + search_terms.get("concepts", []):
            if term.lower() in file_name:
                filename_score += 0.2
        
        # Combine scores with diminishing returns
        total_score = min(
            keyword_score * 0.3 +
            function_score * 0.4 +
            class_score * 0.5 +
            filename_score * 0.3,
            1.0
        )
        
        return total_score
    
    async def _calculate_dependency_score(
        self,
        file_path: str,
        search_terms: Dict[str, List[str]],
        request: ContextRequest
    ) -> float:
        """Calculate dependency score based on import relationships"""
        try:
            dependencies = await self._get_file_dependencies(file_path)
            
            # Score based on dependency relationships
            score = 0.0
            
            # Check if this file imports relevant modules
            for dep in dependencies:
                for keyword in search_terms.get("keywords", []):
                    if keyword.lower() in dep.lower():
                        score += 0.2
                
                for concept in search_terms.get("concepts", []):
                    if concept.lower() in dep.lower():
                        score += 0.3
            
            # Check if file is imported by other relevant files
            reverse_deps = await self._get_reverse_dependencies(file_path)
            for reverse_dep in reverse_deps:
                for pattern in search_terms.get("file_patterns", []):
                    if pattern.lower() in Path(reverse_dep).name.lower():
                        score += 0.25
            
            # Boost score for core project files
            file_path_lower = file_path.lower()
            core_patterns = ['__init__', 'main', 'app', 'core', 'base', 'common']
            for pattern in core_patterns:
                if pattern in file_path_lower:
                    score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating dependency score for {file_path}: {str(e)}")
            return 0.0
    
    async def _calculate_historical_score(
        self,
        file_path: str,
        agent_type: str,
        story_id: str
    ) -> float:
        """Calculate historical access score from agent memory"""
        try:
            if not self.agent_memory:
                return 0.0
            
            # Get historical context snapshots
            snapshots = await self.agent_memory.get_context_history(
                agent_type, story_id, limit=50
            )
            
            if not snapshots:
                return 0.0
            
            # Count file accesses and weight by recency
            access_count = 0
            recent_access_bonus = 0.0
            
            for i, snapshot in enumerate(snapshots):
                if file_path in snapshot.file_list:
                    # Weight more recent accesses higher
                    recency_weight = 1.0 - (i / len(snapshots)) * 0.5
                    access_count += recency_weight
                    
                    # Bonus for very recent access
                    if i < 5:
                        recent_access_bonus += 0.1
            
            # Normalize by total snapshots
            access_rate = access_count / len(snapshots) if snapshots else 0.0
            
            return min(access_rate + recent_access_bonus, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating historical score for {file_path}: {str(e)}")
            return 0.0
    
    async def _calculate_semantic_score(
        self,
        content: str,
        file_type: FileType,
        request: ContextRequest
    ) -> float:
        """Calculate semantic relevance score"""
        try:
            # Simple semantic scoring based on content type and request context
            score = 0.0
            
            # Agent type relevance
            agent_type = request.agent_type.lower()
            content_lower = content.lower()
            
            if agent_type == "codeagent":
                # Favor Python code files
                if file_type == FileType.PYTHON and 'def ' in content_lower:
                    score += 0.4
                if 'class ' in content_lower:
                    score += 0.3
                if 'import ' in content_lower:
                    score += 0.2
            
            elif agent_type == "qaagent":
                # Favor test files
                if file_type == FileType.TEST:
                    score += 0.5
                if any(word in content_lower for word in ['test', 'assert', 'mock', 'fixture']):
                    score += 0.3
            
            elif agent_type == "designagent":
                # Favor documentation and config files
                if file_type in [FileType.MARKDOWN, FileType.CONFIG]:
                    score += 0.4
                if any(word in content_lower for word in ['architecture', 'design', 'specification']):
                    score += 0.3
            
            elif agent_type == "dataagent":
                # Favor data-related files
                if file_type == FileType.JSON:
                    score += 0.3
                if any(word in content_lower for word in ['data', 'schema', 'model', 'database']):
                    score += 0.4
            
            # TDD phase relevance
            if request.task and hasattr(request.task, 'current_state'):
                tdd_state = request.task.current_state
                if tdd_state == TDDState.RED:
                    if file_type == FileType.TEST:
                        score += 0.2
                elif tdd_state == TDDState.GREEN:
                    if file_type == FileType.PYTHON and file_type != FileType.TEST:
                        score += 0.2
                elif tdd_state == TDDState.REFACTOR:
                    if 'refactor' in content_lower or 'cleanup' in content_lower:
                        score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating semantic score: {str(e)}")
            return 0.0
    
    async def _calculate_tdd_phase_score(
        self,
        file_path: str,
        file_type: FileType,
        tdd_phase: TDDState
    ) -> float:
        """Calculate TDD phase relevance score"""
        try:
            score = 0.0
            file_name = Path(file_path).name.lower()
            
            if tdd_phase == TDDState.RED:
                # Favor test files during RED phase
                if file_type == FileType.TEST:
                    score += 0.8
                elif 'test' in file_name:
                    score += 0.6
                elif file_type == FileType.PYTHON and 'test' in file_path.lower():
                    score += 0.4
            
            elif tdd_phase == TDDState.GREEN:
                # Favor implementation files during GREEN phase
                if file_type == FileType.PYTHON and file_type != FileType.TEST:
                    score += 0.8
                elif 'implement' in file_name or 'main' in file_name:
                    score += 0.6
            
            elif tdd_phase == TDDState.REFACTOR:
                # Favor both test and implementation files during REFACTOR
                if file_type in [FileType.PYTHON, FileType.TEST]:
                    score += 0.6
                if any(keyword in file_name for keyword in ['refactor', 'cleanup', 'optimize']):
                    score += 0.8
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating TDD phase score: {str(e)}")
            return 0.0
    
    # Content filtering methods
    
    async def _filter_python_content(
        self,
        content: str,
        request: ContextRequest,
        target_tokens: int
    ) -> str:
        """Filter Python content using AST analysis"""
        try:
            tree = ast.parse(content)
            search_terms = await self._extract_search_terms(request)
            
            # Analyze AST nodes for relevance
            relevant_nodes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    node_relevance = await self._score_python_node(node, search_terms)
                    if node_relevance > 0.1:
                        relevant_nodes.append((node, node_relevance))
            
            # Sort nodes by relevance
            relevant_nodes.sort(key=lambda x: x[1], reverse=True)
            
            # Extract relevant code sections
            filtered_content = []
            current_tokens = 0
            
            for node, relevance in relevant_nodes:
                node_content = ast.get_source_segment(content, node)
                if node_content:
                    node_tokens = await self.token_calculator.estimate_tokens(node_content)
                    if current_tokens + node_tokens <= target_tokens:
                        filtered_content.append(f"# Relevance: {relevance:.2f}")
                        filtered_content.append(node_content)
                        filtered_content.append("")
                        current_tokens += node_tokens
                    else:
                        break
            
            return "\n".join(filtered_content) if filtered_content else content[:target_tokens * 4]
            
        except SyntaxError:
            # Fallback to simple text filtering for invalid Python
            return await self._filter_text_content(content, request, target_tokens)
        except Exception as e:
            logger.warning(f"Error in Python content filtering: {str(e)}")
            return content[:target_tokens * 4]
    
    async def _filter_test_content(
        self,
        content: str,
        request: ContextRequest,
        target_tokens: int
    ) -> str:
        """Filter test content prioritizing relevant test methods"""
        try:
            tree = ast.parse(content)
            search_terms = await self._extract_search_terms(request)
            
            # Find test methods and classes
            test_nodes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    relevance = await self._score_python_node(node, search_terms)
                    test_nodes.append((node, relevance))
                elif isinstance(node, ast.ClassDef) and 'test' in node.name.lower():
                    relevance = await self._score_python_node(node, search_terms)
                    test_nodes.append((node, relevance))
            
            # Sort by relevance and extract content
            test_nodes.sort(key=lambda x: x[1], reverse=True)
            
            filtered_content = []
            current_tokens = 0
            
            # Always include imports first
            imports = [line for line in content.split('\n') if line.strip().startswith('import') or line.strip().startswith('from')]
            if imports:
                import_content = '\n'.join(imports)
                import_tokens = await self.token_calculator.estimate_tokens(import_content)
                if import_tokens <= target_tokens:
                    filtered_content.append(import_content)
                    current_tokens += import_tokens
            
            # Add relevant test methods
            for node, relevance in test_nodes:
                node_content = ast.get_source_segment(content, node)
                if node_content:
                    node_tokens = await self.token_calculator.estimate_tokens(node_content)
                    if current_tokens + node_tokens <= target_tokens:
                        filtered_content.append(f"# Test relevance: {relevance:.2f}")
                        filtered_content.append(node_content)
                        current_tokens += node_tokens
                    else:
                        break
            
            return "\n".join(filtered_content) if filtered_content else content[:target_tokens * 4]
            
        except Exception as e:
            logger.warning(f"Error in test content filtering: {str(e)}")
            return content[:target_tokens * 4]
    
    async def _filter_text_content(
        self,
        content: str,
        request: ContextRequest,
        target_tokens: int
    ) -> str:
        """Filter text content by paragraphs and sections"""
        search_terms = await self._extract_search_terms(request)
        all_terms = (
            search_terms.get("keywords", []) +
            search_terms.get("concepts", []) +
            search_terms.get("function_names", []) +
            search_terms.get("class_names", [])
        )
        
        # Split content into sections
        sections = re.split(r'\n\s*\n', content)
        scored_sections = []
        
        for section in sections:
            if not section.strip():
                continue
                
            # Score section based on term matches
            score = 0.0
            section_lower = section.lower()
            
            for term in all_terms:
                if term.lower() in section_lower:
                    score += 1.0
            
            # Bonus for headers and important sections
            if section.strip().startswith('#'):
                score += 2.0
            elif any(keyword in section_lower for keyword in ['important', 'note', 'warning', 'todo']):
                score += 1.0
            
            scored_sections.append((section, score))
        
        # Sort by relevance and build filtered content
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        
        filtered_content = []
        current_tokens = 0
        
        for section, score in scored_sections:
            section_tokens = await self.token_calculator.estimate_tokens(section)
            if current_tokens + section_tokens <= target_tokens:
                filtered_content.append(section)
                current_tokens += section_tokens
            else:
                break
        
        return "\n\n".join(filtered_content) if filtered_content else content[:target_tokens * 4]
    
    async def _truncate_content(self, content: str, target_tokens: int) -> str:
        """Simple content truncation as fallback"""
        char_limit = target_tokens * 4  # Rough estimation
        if len(content) <= char_limit:
            return content
        
        truncated = content[:char_limit]
        # Try to break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > char_limit * 0.8:
            truncated = truncated[:last_space]
        
        return truncated + "\n... [content truncated]"
    
    async def _score_python_node(
        self,
        node: ast.AST,
        search_terms: Dict[str, List[str]]
    ) -> float:
        """Score Python AST node for relevance"""
        score = 0.0
        
        if isinstance(node, ast.FunctionDef):
            # Check function name against search terms
            for func_name in search_terms.get("function_names", []):
                if func_name.lower() == node.name.lower():
                    score += 1.0
            
            # Check for keyword matches in function name
            for keyword in search_terms.get("keywords", []):
                if keyword.lower() in node.name.lower():
                    score += 0.5
        
        elif isinstance(node, ast.ClassDef):
            # Check class name against search terms
            for class_name in search_terms.get("class_names", []):
                if class_name.lower() == node.name.lower():
                    score += 1.0
            
            # Check for keyword matches in class name
            for keyword in search_terms.get("keywords", []):
                if keyword.lower() in node.name.lower():
                    score += 0.5
        
        return min(score, 1.0)
    
    # Utility methods
    
    async def _get_file_content(self, file_path: str) -> str:
        """Get file content with caching"""
        cache_key = file_path
        
        # Check cache validity
        if cache_key in self._content_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and (datetime.now() - cache_time).seconds < 300:  # 5 minute cache
                self._cache_hits += 1
                return self._content_cache[cache_key]
        
        self._cache_misses += 1
        
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Cache the content
                self._content_cache[cache_key] = content
                self._cache_timestamps[cache_key] = datetime.now()
                
                return content
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {str(e)}")
        
        return ""
    
    async def _get_file_type(self, file_path: str) -> FileType:
        """Determine file type with caching"""
        if file_path in self._file_type_cache:
            return self._file_type_cache[file_path]
        
        path = Path(file_path)
        suffix = path.suffix.lower()
        name = path.name.lower()
        
        # Determine file type
        if suffix == '.py':
            if 'test' in name or name.startswith('test_') or path.parent.name == 'tests':
                file_type = FileType.TEST
            else:
                file_type = FileType.PYTHON
        elif suffix in ['.md', '.rst']:
            file_type = FileType.MARKDOWN
        elif suffix == '.json':
            file_type = FileType.JSON
        elif suffix in ['.yml', '.yaml']:
            file_type = FileType.YAML
        elif suffix in ['.cfg', '.ini', '.conf', '.toml']:
            file_type = FileType.CONFIG
        else:
            file_type = FileType.OTHER
        
        self._file_type_cache[file_path] = file_type
        return file_type
    
    async def _get_file_dependencies(self, file_path: str) -> Set[str]:
        """Get file dependencies with caching"""
        if file_path in self._file_dependencies_cache:
            return self._file_dependencies_cache[file_path]
        
        dependencies = set()
        
        try:
            content = await self._get_file_content(file_path)
            if not content:
                return dependencies
            
            # Extract Python imports
            if file_path.endswith('.py'):
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Simple import parsing
                        if line.startswith('import '):
                            module = line[7:].split()[0].split('.')[0]
                            dependencies.add(module)
                        elif line.startswith('from '):
                            parts = line.split()
                            if len(parts) >= 2:
                                module = parts[1].split('.')[0]
                                dependencies.add(module)
            
            self._file_dependencies_cache[file_path] = dependencies
            
        except Exception as e:
            logger.debug(f"Error extracting dependencies from {file_path}: {str(e)}")
        
        return dependencies
    
    async def _get_reverse_dependencies(self, file_path: str) -> Set[str]:
        """Get files that depend on this file (simplified implementation)"""
        reverse_deps = set()
        
        try:
            # Simple approach: look for files that import this module
            module_name = Path(file_path).stem
            
            # Search in project directory for files that import this module
            for py_file in self.project_path.rglob("*.py"):
                if py_file == Path(file_path):
                    continue
                
                try:
                    content = await self._get_file_content(str(py_file))
                    if f"import {module_name}" in content or f"from {module_name}" in content:
                        reverse_deps.add(str(py_file))
                except Exception:
                    continue
        
        except Exception as e:
            logger.debug(f"Error finding reverse dependencies for {file_path}: {str(e)}")
        
        return reverse_deps
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the filter"""
        avg_filtering_time = (
            sum(self._filtering_times) / len(self._filtering_times)
            if self._filtering_times else 0.0
        )
        
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0 else 0.0
        )
        
        return {
            "average_filtering_time": avg_filtering_time,
            "max_filtering_time": max(self._filtering_times) if self._filtering_times else 0.0,
            "min_filtering_time": min(self._filtering_times) if self._filtering_times else 0.0,
            "total_filtering_operations": len(self._filtering_times),
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cached_files": len(self._content_cache),
            "cached_dependencies": len(self._file_dependencies_cache)
        }
    
    async def clear_cache(self) -> None:
        """Clear all caches"""
        self._content_cache.clear()
        self._file_dependencies_cache.clear()
        self._file_type_cache.clear()
        self._cache_timestamps.clear()
        logger.info("ContextFilter caches cleared")