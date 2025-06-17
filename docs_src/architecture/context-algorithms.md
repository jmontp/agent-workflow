# Context Management Algorithms and Research

## Overview

This document details the core algorithms powering the Context Management System, including relevance scoring, content compression, dependency analysis, and token optimization. Each algorithm is designed to address specific challenges in managing context for AI agents while respecting token limitations.

## Relevance Scoring Algorithm

### Multi-Factor Relevance Scoring

The relevance scoring algorithm combines multiple factors to determine how relevant a file is to the current task context.

```python
def calculate_relevance_score(file_path: str, task: TDDTask, 
                            context: ContextRequest) -> float:
    """
    Calculate multi-factor relevance score (0.0 to 1.0)
    
    Factors:
    - Direct mention (40% weight): File explicitly referenced in task
    - Dependency analysis (25% weight): Code dependencies and imports
    - Historical relevance (20% weight): Past usage patterns
    - Semantic similarity (10% weight): Content similarity to task
    - TDD phase relevance (5% weight): Phase-specific importance
    """
    
    # Factor 1: Direct mention in task description or files
    direct_mention_score = calculate_direct_mention_score(file_path, task)
    
    # Factor 2: Static dependency analysis
    dependency_score = calculate_dependency_score(file_path, task.source_files)
    
    # Factor 3: Historical usage patterns
    historical_score = calculate_historical_relevance(file_path, context.agent_type, task.story_id)
    
    # Factor 4: Semantic content similarity
    semantic_score = calculate_semantic_similarity(file_path, task.description)
    
    # Factor 5: TDD phase-specific relevance
    phase_score = calculate_phase_relevance(file_path, task.current_state)
    
    # Weighted combination
    total_score = (
        0.40 * direct_mention_score +
        0.25 * dependency_score +
        0.20 * historical_score +
        0.10 * semantic_score +
        0.05 * phase_score
    )
    
    # Apply boost factors
    boost_factor = calculate_boost_factors(file_path, task)
    
    return min(1.0, total_score * boost_factor)
```

### Component Algorithms

#### Direct Mention Scoring
```python
def calculate_direct_mention_score(file_path: str, task: TDDTask) -> float:
    """Calculate score based on direct mentions of file in task context"""
    score = 0.0
    
    # Check if file is explicitly mentioned in task description
    if file_path in task.description or os.path.basename(file_path) in task.description:
        score += 0.8
    
    # Check if file is in task source files
    if file_path in task.source_files:
        score += 1.0
    
    # Check if file is in test files
    if file_path in task.test_files:
        score += 0.9
    
    # Check for file name mentions in acceptance criteria
    for criteria in task.acceptance_criteria:
        if os.path.basename(file_path) in criteria:
            score += 0.6
    
    return min(1.0, score)
```

#### Dependency Analysis Scoring
```python
def calculate_dependency_score(file_path: str, source_files: List[str]) -> float:
    """Calculate relevance based on code dependencies"""
    
    # Get direct dependencies (imports)
    direct_deps = get_direct_dependencies(file_path)
    
    # Get reverse dependencies (what imports this file)
    reverse_deps = get_reverse_dependencies(file_path)
    
    # Calculate overlap with task source files
    source_set = set(source_files)
    
    # Score based on direct dependencies overlap
    direct_overlap = len(set(direct_deps) & source_set) / max(len(direct_deps), 1)
    
    # Score based on reverse dependencies overlap
    reverse_overlap = len(set(reverse_deps) & source_set) / max(len(reverse_deps), 1)
    
    # Calculate transitive dependency score
    transitive_score = calculate_transitive_dependency_score(file_path, source_files, max_depth=3)
    
    # Weighted combination
    dependency_score = (
        0.5 * direct_overlap +
        0.3 * reverse_overlap +
        0.2 * transitive_score
    )
    
    return dependency_score

def get_direct_dependencies(file_path: str) -> List[str]:
    """Extract direct dependencies from Python file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
        
        # Convert module names to file paths
        return resolve_module_paths(dependencies, file_path)
        
    except Exception:
        return []
```

#### Historical Relevance Scoring
```python
def calculate_historical_relevance(file_path: str, agent_type: str, story_id: str) -> float:
    """Calculate relevance based on historical usage patterns"""
    
    # Get historical access patterns
    access_history = get_file_access_history(file_path, agent_type)
    
    # Get similar story patterns
    similar_stories = get_similar_story_files(story_id, file_path)
    
    # Calculate access frequency score
    frequency_score = calculate_access_frequency_score(access_history)
    
    # Calculate recency score (more recent = higher score)
    recency_score = calculate_recency_score(access_history)
    
    # Calculate similar story score
    similarity_score = calculate_story_similarity_score(similar_stories)
    
    # Weighted combination
    historical_score = (
        0.4 * frequency_score +
        0.3 * recency_score +
        0.3 * similarity_score
    )
    
    return historical_score

def calculate_access_frequency_score(access_history: List[Dict]) -> float:
    """Score based on how frequently file has been accessed"""
    if not access_history:
        return 0.0
    
    # Count accesses in different time windows
    now = datetime.utcnow()
    
    recent_accesses = sum(1 for access in access_history 
                         if (now - access['timestamp']).days <= 7)
    total_accesses = len(access_history)
    
    # Normalize based on total project activity
    project_activity = get_project_activity_baseline()
    
    frequency_ratio = total_accesses / max(project_activity, 1)
    recency_boost = min(1.0, recent_accesses / 5)  # Boost for recent activity
    
    return min(1.0, frequency_ratio * (1.0 + recency_boost))
```

#### Semantic Similarity Scoring
```python
def calculate_semantic_similarity(file_path: str, task_description: str) -> float:
    """Calculate semantic similarity between file content and task description"""
    
    # Extract key content from file
    file_content = extract_file_summary(file_path)
    
    # Use sentence embeddings for similarity
    task_embedding = get_sentence_embedding(task_description)
    file_embedding = get_sentence_embedding(file_content)
    
    # Calculate cosine similarity
    similarity = cosine_similarity(task_embedding, file_embedding)
    
    # Apply content type boosts
    content_boost = get_content_type_boost(file_path, task_description)
    
    return min(1.0, similarity * content_boost)

def extract_file_summary(file_path: str) -> str:
    """Extract meaningful summary from file for semantic analysis"""
    
    if file_path.endswith('.py'):
        return extract_python_summary(file_path)
    elif file_path.endswith('.md'):
        return extract_markdown_summary(file_path)
    elif file_path.endswith(('.yml', '.yaml')):
        return extract_yaml_summary(file_path)
    else:
        return extract_generic_summary(file_path)

def extract_python_summary(file_path: str) -> str:
    """Extract Python file summary including docstrings and key elements"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        summary_parts = []
        
        # Extract module docstring
        if ast.get_docstring(tree):
            summary_parts.append(ast.get_docstring(tree))
        
        # Extract class and function names and docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                summary_parts.append(node.name)
                if ast.get_docstring(node):
                    summary_parts.append(ast.get_docstring(node))
        
        # Extract comments
        comments = extract_comments(content)
        summary_parts.extend(comments)
        
        return ' '.join(summary_parts)
        
    except Exception:
        return ""
```

## Content Compression Algorithms

### Adaptive Python Code Compression

```python
def compress_python_code(content: str, target_tokens: int, 
                        preserve_structure: bool = True) -> CompressionResult:
    """
    Compress Python code while preserving semantic meaning and structure
    
    Compression Strategy:
    1. Parse AST to understand code structure
    2. Identify critical elements (classes, functions, key logic)
    3. Remove or summarize non-critical elements
    4. Reconstruct code with preserved structure
    """
    
    original_tokens = estimate_tokens(content)
    
    if original_tokens <= target_tokens:
        return CompressionResult(
            compressed_content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            compression_ratio=1.0,
            semantic_preservation_score=1.0
        )
    
    # Parse code into AST
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Fallback to line-based compression for invalid syntax
        return compress_python_lines(content, target_tokens)
    
    # Analyze code elements
    elements = analyze_code_elements(tree)
    
    # Determine compression strategy based on target ratio
    target_ratio = target_tokens / original_tokens
    compression_strategy = select_compression_strategy(target_ratio)
    
    # Apply compression strategy
    compressed_tree = apply_compression_strategy(tree, elements, compression_strategy)
    
    # Reconstruct code
    compressed_content = ast.unparse(compressed_tree)
    compressed_tokens = estimate_tokens(compressed_content)
    
    # Calculate semantic preservation score
    semantic_score = calculate_semantic_preservation(content, compressed_content)
    
    return CompressionResult(
        compressed_content=compressed_content,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        compression_ratio=original_tokens / compressed_tokens,
        semantic_preservation_score=semantic_score
    )

def analyze_code_elements(tree: ast.AST) -> Dict[str, List]:
    """Analyze and categorize code elements by importance"""
    elements = {
        'critical': [],      # Core classes, main functions
        'important': [],     # Helper functions, key methods
        'standard': [],      # Regular methods, properties
        'optional': [],      # Comments, docstrings, debug code
        'removable': []      # Dead code, unused imports
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            importance = classify_class_importance(node)
            elements[importance].append(node)
        elif isinstance(node, ast.FunctionDef):
            importance = classify_function_importance(node)
            elements[importance].append(node)
        elif isinstance(node, ast.Import):
            if is_unused_import(node, tree):
                elements['removable'].append(node)
            else:
                elements['standard'].append(node)
    
    return elements

def select_compression_strategy(target_ratio: float) -> str:
    """Select compression strategy based on target compression ratio"""
    if target_ratio > 0.8:
        return 'conservative'  # Remove only comments and dead code
    elif target_ratio > 0.6:
        return 'moderate'      # Remove optional elements, compress docstrings
    elif target_ratio > 0.4:
        return 'aggressive'    # Keep only critical and important elements
    else:
        return 'extreme'       # Keep only critical elements, summarize everything else

def apply_compression_strategy(tree: ast.AST, elements: Dict, strategy: str) -> ast.AST:
    """Apply selected compression strategy to AST"""
    
    if strategy == 'conservative':
        return compress_conservative(tree, elements)
    elif strategy == 'moderate':
        return compress_moderate(tree, elements)
    elif strategy == 'aggressive':
        return compress_aggressive(tree, elements)
    elif strategy == 'extreme':
        return compress_extreme(tree, elements)
    
    return tree

def compress_conservative(tree: ast.AST, elements: Dict) -> ast.AST:
    """Conservative compression: remove only non-essential elements"""
    transformer = ConservativeTransformer(elements)
    return transformer.visit(tree)

class ConservativeTransformer(ast.NodeTransformer):
    def __init__(self, elements):
        self.elements = elements
    
    def visit_FunctionDef(self, node):
        # Remove docstrings but keep function structure
        if ast.get_docstring(node):
            node.body = [stmt for stmt in node.body 
                        if not isinstance(stmt, ast.Expr) or 
                        not isinstance(stmt.value, ast.Constant)]
        
        # Remove comments (handled at line level)
        return self.generic_visit(node)
    
    def visit_Import(self, node):
        # Remove unused imports
        if node in self.elements['removable']:
            return None
        return node
```

### Test File Compression

```python
def compress_test_file(content: str, target_tokens: int) -> CompressionResult:
    """
    Compress test files while preserving test intent and assertions
    
    Strategy:
    1. Preserve all test method signatures
    2. Preserve all assertions
    3. Compress setup/teardown code
    4. Summarize test data and mocks
    """
    
    original_tokens = estimate_tokens(content)
    
    if original_tokens <= target_tokens:
        return CompressionResult(
            compressed_content=content,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
            compression_ratio=1.0
        )
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return compress_test_lines(content, target_tokens)
    
    # Identify test structure
    test_structure = analyze_test_structure(tree)
    
    # Compress based on test elements
    compressed_tree = compress_test_elements(tree, test_structure, target_tokens)
    
    compressed_content = ast.unparse(compressed_tree)
    compressed_tokens = estimate_tokens(compressed_content)
    
    return CompressionResult(
        compressed_content=compressed_content,
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        compression_ratio=original_tokens / compressed_tokens
    )

def analyze_test_structure(tree: ast.AST) -> Dict:
    """Analyze test file structure and categorize elements"""
    structure = {
        'test_methods': [],
        'setup_methods': [],
        'helper_methods': [],
        'assertions': [],
        'test_data': [],
        'imports': []
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                structure['test_methods'].append(node)
                # Extract assertions from test method
                assertions = extract_assertions(node)
                structure['assertions'].extend(assertions)
            elif node.name in ['setUp', 'tearDown', 'setUpClass', 'tearDownClass']:
                structure['setup_methods'].append(node)
            else:
                structure['helper_methods'].append(node)
    
    return structure

def extract_assertions(test_method: ast.FunctionDef) -> List[ast.stmt]:
    """Extract assertion statements from test method"""
    assertions = []
    
    for node in ast.walk(test_method):
        if isinstance(node, ast.Call):
            if (isinstance(node.func, ast.Attribute) and 
                node.func.attr.startswith('assert')):
                assertions.append(node)
        elif isinstance(node, ast.Assert):
            assertions.append(node)
    
    return assertions
```

## Token Budget Allocation Algorithm

### Dynamic Budget Allocation

```python
def calculate_optimal_budget(total_tokens: int, 
                           context_components: Dict[str, Any],
                           agent_type: str,
                           tdd_phase: TDDState) -> TokenBudget:
    """
    Calculate optimal token budget allocation based on:
    - Available content in each category
    - Agent type preferences
    - TDD phase requirements
    - Historical usage patterns
    """
    
    # Base allocation percentages by agent type
    base_allocations = get_agent_base_allocations(agent_type)
    
    # Adjust allocations based on TDD phase
    phase_adjustments = get_phase_adjustments(tdd_phase)
    
    # Apply adjustments
    adjusted_allocations = apply_allocation_adjustments(base_allocations, phase_adjustments)
    
    # Calculate actual needs vs available content
    component_needs = calculate_component_needs(context_components)
    
    # Optimize allocation based on needs
    optimized_budget = optimize_budget_allocation(
        total_tokens, adjusted_allocations, component_needs
    )
    
    return optimized_budget

def get_agent_base_allocations(agent_type: str) -> Dict[str, float]:
    """Get base allocation percentages for different agent types"""
    allocations = {
        'DesignAgent': {
            'core_context': 0.30,
            'dependencies': 0.15,
            'historical': 0.25,
            'agent_memory': 0.15,
            'documentation': 0.10,
            'buffer': 0.05
        },
        'QAAgent': {
            'core_context': 0.45,  # Tests need more specific context
            'dependencies': 0.20,
            'historical': 0.15,
            'agent_memory': 0.10,
            'documentation': 0.05,
            'buffer': 0.05
        },
        'CodeAgent': {
            'core_context': 0.40,
            'dependencies': 0.25,  # Code needs more dependency context
            'historical': 0.15,
            'agent_memory': 0.10,
            'documentation': 0.05,
            'buffer': 0.05
        },
        'DataAgent': {
            'core_context': 0.35,
            'dependencies': 0.10,
            'historical': 0.30,    # Data analysis benefits from historical patterns
            'agent_memory': 0.15,
            'documentation': 0.05,
            'buffer': 0.05
        }
    }
    
    return allocations.get(agent_type, allocations['CodeAgent'])

def get_phase_adjustments(tdd_phase: TDDState) -> Dict[str, float]:
    """Get allocation adjustments based on TDD phase"""
    adjustments = {
        TDDState.DESIGN: {
            'documentation': 1.5,  # Boost documentation for design
            'historical': 1.3,     # Boost historical patterns
            'dependencies': 0.8    # Reduce dependency focus
        },
        TDDState.TEST_RED: {
            'core_context': 1.4,   # Boost current context for test writing
            'agent_memory': 1.2,   # Boost memory for test patterns
            'dependencies': 0.9    # Slight reduction in dependencies
        },
        TDDState.CODE_GREEN: {
            'dependencies': 1.4,   # Boost dependencies for implementation
            'core_context': 1.2,   # Boost current context
            'historical': 0.8      # Reduce historical patterns
        },
        TDDState.REFACTOR: {
            'historical': 1.5,     # Boost historical patterns for best practices
            'agent_memory': 1.3,   # Boost memory for refactoring patterns
            'core_context': 1.1    # Slight boost to current context
        },
        TDDState.COMMIT: {
            'core_context': 1.3,   # Boost current context for commit validation
            'dependencies': 1.1,   # Slight boost for integration validation
            'agent_memory': 0.9    # Slight reduction in memory
        }
    }
    
    return adjustments.get(tdd_phase, {})

def optimize_budget_allocation(total_tokens: int, 
                             base_allocations: Dict[str, float],
                             component_needs: Dict[str, int]) -> TokenBudget:
    """
    Optimize budget allocation by redistributing unused allocations
    and handling over-allocations
    """
    
    # Calculate initial allocations
    initial_budget = {}
    for component, percentage in base_allocations.items():
        initial_budget[component] = int(total_tokens * percentage)
    
    # Identify over and under allocations
    adjustments = {}
    unused_tokens = 0
    needed_tokens = 0
    
    for component, allocated in initial_budget.items():
        needed = component_needs.get(component, 0)
        
        if needed == 0:
            # No content available, free up allocation
            unused_tokens += allocated
            adjustments[component] = 0
        elif needed < allocated:
            # Less content than allocation, free up excess
            excess = allocated - needed
            unused_tokens += excess
            adjustments[component] = needed
        elif needed > allocated:
            # More content than allocation, track need
            deficit = needed - allocated
            needed_tokens += deficit
            adjustments[component] = allocated
        else:
            # Perfect match
            adjustments[component] = allocated
    
    # Redistribute unused tokens to components that need more
    if unused_tokens > 0 and needed_tokens > 0:
        redistribution_ratio = min(1.0, unused_tokens / needed_tokens)
        
        for component, allocated in adjustments.items():
            needed = component_needs.get(component, 0)
            if needed > allocated:
                additional = int((needed - allocated) * redistribution_ratio)
                adjustments[component] += additional
                unused_tokens -= additional
    
    # Any remaining unused tokens go to buffer
    adjustments['buffer'] = adjustments.get('buffer', 0) + unused_tokens
    
    return TokenBudget(
        total_budget=total_tokens,
        core_context=adjustments.get('core_context', 0),
        dependencies=adjustments.get('dependencies', 0),
        agent_memory=adjustments.get('agent_memory', 0),
        metadata=adjustments.get('documentation', 0),
        buffer=adjustments.get('buffer', 0)
    )
```

## Dependency Analysis Algorithm

### Static Dependency Analysis

```python
def build_dependency_graph(project_path: str) -> Dict[str, Set[str]]:
    """
    Build comprehensive dependency graph for project
    
    Returns:
        Dict mapping file paths to sets of their dependencies
    """
    
    dependency_graph = {}
    
    # Find all Python files
    python_files = find_python_files(project_path)
    
    for file_path in python_files:
        dependencies = extract_file_dependencies(file_path, project_path)
        dependency_graph[file_path] = set(dependencies)
    
    # Add reverse dependencies
    reverse_graph = build_reverse_dependencies(dependency_graph)
    
    return {
        'forward': dependency_graph,
        'reverse': reverse_graph
    }

def extract_file_dependencies(file_path: str, project_root: str) -> List[str]:
    """Extract dependencies from a single Python file"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dep_path = resolve_import_path(alias.name, file_path, project_root)
                    if dep_path:
                        dependencies.append(dep_path)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dep_path = resolve_import_path(node.module, file_path, project_root)
                    if dep_path:
                        dependencies.append(dep_path)
        
        return dependencies
        
    except Exception as e:
        logger.warning(f"Could not analyze dependencies for {file_path}: {e}")
        return []

def resolve_import_path(module_name: str, source_file: str, project_root: str) -> Optional[str]:
    """Resolve import module name to actual file path"""
    
    # Handle relative imports
    if module_name.startswith('.'):
        return resolve_relative_import(module_name, source_file, project_root)
    
    # Handle absolute imports within project
    if is_project_module(module_name, project_root):
        return resolve_project_import(module_name, project_root)
    
    # External dependencies (not resolved to file paths)
    return None

def calculate_transitive_dependencies(file_path: str, 
                                    dependency_graph: Dict[str, Set[str]], 
                                    max_depth: int = 3) -> Set[str]:
    """Calculate transitive dependencies up to max_depth"""
    
    visited = set()
    to_visit = [(file_path, 0)]
    transitive_deps = set()
    
    while to_visit:
        current_file, depth = to_visit.pop(0)
        
        if current_file in visited or depth >= max_depth:
            continue
        
        visited.add(current_file)
        
        # Get direct dependencies
        direct_deps = dependency_graph.get(current_file, set())
        
        for dep in direct_deps:
            if dep not in visited:
                transitive_deps.add(dep)
                to_visit.append((dep, depth + 1))
    
    return transitive_deps

def calculate_dependency_impact_score(file_path: str, 
                                    dependency_graph: Dict[str, Set[str]]) -> float:
    """
    Calculate impact score based on how many files depend on this file
    Higher score = more files depend on this file
    """
    
    reverse_deps = dependency_graph.get('reverse', {}).get(file_path, set())
    
    # Calculate direct impact
    direct_impact = len(reverse_deps)
    
    # Calculate transitive impact (files that depend on dependents)
    transitive_impact = 0
    for dep_file in reverse_deps:
        transitive_deps = dependency_graph.get('reverse', {}).get(dep_file, set())
        transitive_impact += len(transitive_deps)
    
    # Normalize impact score
    max_files = len(dependency_graph.get('forward', {}))
    if max_files == 0:
        return 0.0
    
    # Weight direct impact more heavily than transitive
    total_impact = direct_impact + (0.5 * transitive_impact)
    normalized_score = min(1.0, total_impact / max_files)
    
    return normalized_score
```

## Caching and Performance Algorithms

### Intelligent Cache Management

```python
class IntelligentCache:
    """
    Intelligent caching system with predictive pre-loading and adaptive eviction
    """
    
    def __init__(self, max_size_mb: int = 1000):
        self.max_size_mb = max_size_mb
        self.cache = {}
        self.access_patterns = {}
        self.prediction_model = CachePredictor()
    
    async def get_context(self, request: ContextRequest) -> Optional[AgentContext]:
        """Get context from cache with pattern learning"""
        
        cache_key = self.generate_cache_key(request)
        
        # Record access pattern
        self.record_access_pattern(cache_key, request)
        
        # Check cache
        if cache_key in self.cache:
            context = self.cache[cache_key]
            if self.is_context_valid(context, request):
                self.update_access_time(cache_key)
                return context
        
        return None
    
    async def store_context(self, request: ContextRequest, context: AgentContext):
        """Store context with intelligent eviction"""
        
        cache_key = self.generate_cache_key(request)
        
        # Check if we need to evict items
        if self.should_evict():
            await self.intelligent_eviction()
        
        # Store context
        self.cache[cache_key] = context
        self.update_cache_metadata(cache_key, context)
        
        # Trigger predictive caching
        await self.predictive_cache_warming(request)
    
    def generate_cache_key(self, request: ContextRequest) -> str:
        """Generate cache key considering context factors"""
        
        # Include factors that affect context relevance
        factors = [
            request.agent_type,
            request.story_id,
            request.task.current_state.value,
            hash(tuple(sorted(request.task.source_files))),
            hash(tuple(sorted(request.task.test_files))),
            request.compression_level
        ]
        
        return hashlib.md5(str(factors).encode()).hexdigest()
    
    def is_context_valid(self, context: AgentContext, request: ContextRequest) -> bool:
        """Check if cached context is still valid"""
        
        # Check context age
        context_age = datetime.utcnow() - context.created_at
        if context_age > timedelta(hours=24):
            return False
        
        # Check if source files have changed
        if self.have_files_changed(context.source_files):
            return False
        
        # Check if task requirements have significantly changed
        if self.has_task_changed_significantly(context.task_hash, request.task):
            return False
        
        return True
    
    async def intelligent_eviction(self):
        """Evict cache items using intelligent strategy"""
        
        # Calculate eviction scores for all cached items
        eviction_scores = {}
        
        for cache_key, context in self.cache.items():
            score = self.calculate_eviction_score(cache_key, context)
            eviction_scores[cache_key] = score
        
        # Sort by eviction score (higher = more likely to evict)
        sorted_items = sorted(eviction_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Evict items until we're under the size limit
        current_size = self.get_cache_size_mb()
        target_size = self.max_size_mb * 0.8  # Leave 20% buffer
        
        for cache_key, score in sorted_items:
            if current_size <= target_size:
                break
            
            context = self.cache.pop(cache_key)
            current_size -= self.estimate_context_size_mb(context)
            
            logger.debug(f"Evicted cache item {cache_key} (score: {score:.2f})")
    
    def calculate_eviction_score(self, cache_key: str, context: AgentContext) -> float:
        """Calculate eviction score (higher = more likely to evict)"""
        
        # Factor 1: Age (older = higher eviction score)
        age_hours = (datetime.utcnow() - context.created_at).total_seconds() / 3600
        age_score = min(1.0, age_hours / 24)  # Normalize to 24 hours
        
        # Factor 2: Access frequency (less frequent = higher eviction score)
        access_count = self.access_patterns.get(cache_key, {}).get('count', 0)
        max_access = max((p.get('count', 0) for p in self.access_patterns.values()), default=1)
        frequency_score = 1.0 - (access_count / max_access)
        
        # Factor 3: Size (larger = higher eviction score for equal other factors)
        size_mb = self.estimate_context_size_mb(context)
        max_size = max((self.estimate_context_size_mb(c) for c in self.cache.values()), default=1)
        size_score = size_mb / max_size
        
        # Factor 4: Prediction score (less likely to be accessed = higher eviction score)
        prediction_score = 1.0 - self.prediction_model.predict_access_probability(cache_key)
        
        # Weighted combination
        eviction_score = (
            0.3 * age_score +
            0.3 * frequency_score +
            0.2 * size_score +
            0.2 * prediction_score
        )
        
        return eviction_score
    
    async def predictive_cache_warming(self, request: ContextRequest):
        """Pre-warm cache with likely future requests"""
        
        # Predict likely next requests based on current request
        predicted_requests = self.prediction_model.predict_next_requests(request)
        
        for predicted_request in predicted_requests:
            cache_key = self.generate_cache_key(predicted_request)
            
            # Only pre-warm if not already cached and high confidence
            if cache_key not in self.cache and predicted_request.confidence > 0.7:
                try:
                    # Prepare context in background
                    context = await self.context_manager.prepare_context(predicted_request)
                    await self.store_context(predicted_request, context)
                    
                    logger.debug(f"Pre-warmed cache for predicted request: {cache_key}")
                    
                except Exception as e:
                    logger.warning(f"Failed to pre-warm cache: {e}")

class CachePredictor:
    """Predict future cache access patterns"""
    
    def __init__(self):
        self.pattern_history = []
        self.transition_matrix = {}
    
    def predict_access_probability(self, cache_key: str) -> float:
        """Predict probability that cache_key will be accessed soon"""
        
        # Use simple frequency-based prediction for now
        # Can be enhanced with ML models
        
        recent_accesses = self.get_recent_access_patterns()
        if not recent_accesses:
            return 0.5  # Default probability
        
        # Count how often this key appears in recent patterns
        appearances = sum(1 for pattern in recent_accesses if cache_key in pattern)
        probability = appearances / len(recent_accesses)
        
        return probability
    
    def predict_next_requests(self, current_request: ContextRequest) -> List[ContextRequest]:
        """Predict likely next context requests"""
        
        predictions = []
        
        # Pattern 1: Same agent, next TDD phase
        next_phase = self.get_next_tdd_phase(current_request.task.current_state)
        if next_phase:
            predicted_request = self.create_predicted_request(
                current_request, tdd_phase=next_phase, confidence=0.8
            )
            predictions.append(predicted_request)
        
        # Pattern 2: Different agent, same phase (parallel work)
        for agent_type in ['DesignAgent', 'QAAgent', 'CodeAgent', 'DataAgent']:
            if agent_type != current_request.agent_type:
                predicted_request = self.create_predicted_request(
                    current_request, agent_type=agent_type, confidence=0.6
                )
                predictions.append(predicted_request)
        
        # Pattern 3: Same agent, related story
        related_stories = self.get_related_stories(current_request.story_id)
        for story_id in related_stories[:2]:  # Limit to top 2 related
            predicted_request = self.create_predicted_request(
                current_request, story_id=story_id, confidence=0.4
            )
            predictions.append(predicted_request)
        
        return predictions
```

This comprehensive set of algorithms provides the foundation for intelligent context management, covering relevance scoring, content compression, dependency analysis, and caching strategies. Each algorithm is designed to be configurable and extensible, allowing for continuous improvement based on real-world usage patterns.