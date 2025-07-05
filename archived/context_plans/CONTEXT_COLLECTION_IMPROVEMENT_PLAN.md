# Context Collection Quality Improvement Plan

## Executive Summary

After analyzing the Context Manager's current relevance scoring implementation, I've identified several areas where the scoring is too simplistic and produces suboptimal results. This plan outlines specific, practical improvements to enhance context collection quality without adding unnecessary complexity.

## Current Issues Identified

### 1. Simplistic Keyword Matching (Lines 1750-1759)
**Problem**: Basic word splitting and stopword filtering misses important context
- No stemming or lemmatization (e.g., "authenticate" vs "authentication")
- Ignores compound terms (e.g., "context_manager" becomes "context" and "manager")
- No recognition of technical acronyms or abbreviations

**Example**: Task "fix JWT authentication in user login" extracts ["authentication", "user", "login"] but misses "JWT" (too short)

### 2. Hardcoded Relevance Scores (Lines 2041-2102)
**Problem**: Fixed scores don't adapt to task complexity or project structure
- Direct concept match: always 0.9
- Description match: capped at 0.7 (matching_terms * 0.2)
- Folder relevance: capped at 0.5 (matching_terms * 0.15)
- Function/class name match: 0.5-0.85 based on substring ratio

**Example**: A critical authentication file with description match gets 0.7 while a tangentially related concept file gets 0.9

### 3. Linear Scoring Without Context (Lines 2126-2164)
**Problem**: Relevance calculation doesn't consider relationships between items
- Keywords: 30% weight
- Concepts: 40% weight  
- Actions: 20% weight
- Tags: 10% weight

**Example**: Files imported by relevant files get no boost; test files for relevant code get no association

### 4. Missing File Relationship Analysis
**Problem**: No consideration of code dependencies or file proximity
- Ignores import statements and module dependencies
- No boost for files in same directory
- No penalty for archived or deprecated code

### 5. Poor Task Understanding (Lines 1750-1811)
**Problem**: Heuristic task analysis misses nuance
- Action verbs are hardcoded and limited
- No understanding of task urgency or scope
- File pattern inference is rigid and rule-based

## Specific Improvements

### 1. Enhanced Keyword Extraction

**Location**: `_analyze_task()` method (lines 1750-1759)

**Current Code**:
```python
keywords = []
for word in words:
    clean_word = word.strip('.,!?;:"\'()')
    if len(clean_word) > 3 and clean_word not in self.STOPWORDS:
        keywords.append(clean_word)
```

**Improved Code**:
```python
def _extract_keywords(self, text: str) -> List[str]:
    """Extract keywords with better NLP techniques."""
    keywords = []
    
    # Extract potential compound terms first
    compound_patterns = [
        r'\b[a-z]+_[a-z]+\b',  # snake_case
        r'\b[A-Z][a-z]+[A-Z][a-z]+\b',  # CamelCase
        r'\b[A-Z]+\b',  # ACRONYMS
    ]
    
    for pattern in compound_patterns:
        compounds = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(compounds)
    
    # Extract regular words with stemming
    words = text.lower().split()
    for word in words:
        clean_word = word.strip('.,!?;:"\'()[]{}')
        
        # Keep short technical terms
        if len(clean_word) >= 2 and clean_word.isupper():
            keywords.append(clean_word)
        elif len(clean_word) > 3 and clean_word not in self.STOPWORDS:
            # Add both original and stemmed version
            keywords.append(clean_word)
            stemmed = self._simple_stem(clean_word)
            if stemmed != clean_word:
                keywords.append(stemmed)
    
    return list(set(keywords))  # Remove duplicates

def _simple_stem(self, word: str) -> str:
    """Simple stemming for common patterns."""
    suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'ment']
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) - len(suffix) > 3:
            return word[:-len(suffix)]
    return word
```

### 2. Dynamic Relevance Scoring

**Location**: `_collect_relevant_items()` method (lines 2035-2102)

**Improved Approach**:
```python
def _calculate_dynamic_relevance(self, item, task_analysis, context_items_so_far):
    """Calculate relevance with dynamic weighting based on context."""
    base_score = 0.0
    
    # 1. Concept match scoring (dynamic based on concept importance)
    if hasattr(item, 'path'):
        for concept in task_analysis.concepts:
            if self._item_matches_concept(item, concept):
                # Weight by concept frequency in codebase
                concept_weight = self._get_concept_importance(concept)
                base_score += 0.4 * concept_weight
    
    # 2. Recency boost for modified files
    if hasattr(item, 'last_modified'):
        days_old = (datetime.now() - item.last_modified).days
        recency_boost = max(0, 1 - (days_old / 30))  # Linear decay over 30 days
        base_score += 0.1 * recency_boost
    
    # 3. Import relationship boost
    if hasattr(item, 'path'):
        import_score = self._calculate_import_relevance(item.path, context_items_so_far)
        base_score += 0.2 * import_score
    
    # 4. Directory proximity boost
    if hasattr(item, 'path'):
        proximity_score = self._calculate_proximity_score(item.path, context_items_so_far)
        base_score += 0.1 * proximity_score
    
    # 5. Task-specific adjustments
    if 'fix' in task_analysis.actions and self._is_test_file(item.path):
        base_score *= 1.2  # Boost test files for bug fixes
    elif 'implement' in task_analysis.actions and self._is_interface_file(item.path):
        base_score *= 1.3  # Boost interfaces for new implementations
    
    return min(1.0, base_score)
```

### 3. Smarter File Pattern Matching

**Location**: `_infer_file_patterns()` method (lines 1813-1857)

**Improvements**:
```python
def _infer_file_patterns(self, keywords: List[str], actions: List[str], concepts: List[str]) -> List[str]:
    """Infer file patterns with context awareness."""
    patterns = []
    
    # Learn patterns from project history
    if self.project_index:
        # Get patterns from similar past tasks
        similar_patterns = self._get_patterns_from_similar_tasks(keywords, actions)
        patterns.extend(similar_patterns)
    
    # Smart pattern generation based on keywords
    for keyword in keywords:
        # Check if keyword matches known module/class names
        if keyword in self.project_index.classes:
            file_path = self.project_index.classes[keyword]
            patterns.append(os.path.basename(file_path))
            patterns.append(f"*{keyword}*.py")
        
        if keyword in self.project_index.functions:
            file_path = self.project_index.functions[keyword]
            patterns.append(os.path.basename(file_path))
    
    # Action-based patterns with project conventions
    if 'test' in actions:
        test_patterns = self._discover_test_patterns()
        patterns.extend(test_patterns)
    
    return self._rank_patterns_by_frequency(patterns)
```

### 4. Context-Aware Scoring

**Location**: New method to be added

```python
def _calculate_import_relevance(self, file_path: str, selected_items: List[Any]) -> float:
    """Calculate relevance based on import relationships."""
    if not self.project_index or file_path not in self.project_index.code_files:
        return 0.0
    
    code_meta = self.project_index.code_files[file_path]
    import_score = 0.0
    
    # Check if this file imports any already selected files
    for item in selected_items:
        if hasattr(item, 'path') and item.path in code_meta.imports:
            import_score += 0.3
        
        # Check if any selected file imports this file
        if hasattr(item, 'path') and item.path in self.project_index.code_files:
            other_meta = self.project_index.code_files[item.path]
            if file_path in other_meta.imports:
                import_score += 0.5  # Higher score for being imported
    
    return min(1.0, import_score)

def _calculate_proximity_score(self, file_path: str, selected_items: List[Any]) -> float:
    """Calculate score based on directory proximity."""
    if not selected_items:
        return 0.0
    
    dir_path = os.path.dirname(file_path)
    proximity_score = 0.0
    
    for item in selected_items:
        if hasattr(item, 'path'):
            item_dir = os.path.dirname(item.path)
            if dir_path == item_dir:
                proximity_score += 0.5  # Same directory
            elif self._are_sibling_dirs(dir_path, item_dir):
                proximity_score += 0.3  # Sibling directories
            elif self._is_parent_child(dir_path, item_dir):
                proximity_score += 0.2  # Parent/child relationship
    
    return min(1.0, proximity_score / len(selected_items))
```

### 5. Task Understanding Enhancement

**Location**: `_analyze_task()` method enhancement

```python
def _analyze_task(self, task_description: str) -> TaskAnalysis:
    """Enhanced task analysis with better understanding."""
    # Extract keywords with new method
    keywords = self._extract_keywords(task_description)
    
    # Detect urgency indicators
    urgency_indicators = ['urgent', 'asap', 'critical', 'immediately', 'quick']
    urgency = any(indicator in task_description.lower() for indicator in urgency_indicators)
    
    # Detect scope indicators
    scope_indicators = {
        'narrow': ['specific', 'single', 'one', 'particular', 'this'],
        'broad': ['all', 'entire', 'whole', 'system', 'refactor', 'redesign'],
        'medium': ['several', 'multiple', 'related', 'module']
    }
    
    estimated_scope = self._estimate_scope(task_description, scope_indicators)
    
    # Extract file references
    file_references = self._extract_file_references(task_description)
    if file_references:
        keywords.extend(file_references)
    
    # Match against historical patterns
    if self.contexts:
        similar_tasks = self._find_similar_historical_tasks(task_description)
        if similar_tasks:
            # Learn from past successful contexts
            historical_keywords = self._extract_keywords_from_contexts(similar_tasks)
            keywords.extend(historical_keywords[:5])  # Add top 5
    
    # ... rest of the method
```

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. Enhanced keyword extraction with compound terms and acronyms
2. Dynamic relevance scoring based on file recency
3. Import relationship analysis

### Phase 2: Medium Improvements (3-5 days)  
1. Directory proximity scoring
2. Historical pattern learning
3. Task urgency and scope detection

### Phase 3: Advanced Features (1 week)
1. ML-based relevance learning from successful tasks
2. Project-specific pattern discovery
3. Real-time relevance adjustment based on agent feedback

## Testing Strategy

### Unit Tests
```python
def test_keyword_extraction():
    cm = ContextManager()
    keywords = cm._extract_keywords("Fix JWT authentication in user_login module")
    assert "JWT" in keywords
    assert "authentication" in keywords
    assert "user_login" in keywords
    assert "auth" in keywords  # Stemmed version

def test_import_relevance():
    cm = ContextManager()
    # Setup test project index
    score = cm._calculate_import_relevance("auth.py", [mock_item("login.py")])
    assert score > 0.5  # Should be high if login imports auth

def test_proximity_scoring():
    cm = ContextManager()
    score = cm._calculate_proximity_score(
        "src/auth/token.py", 
        [mock_item("src/auth/login.py")]
    )
    assert score == 0.5  # Same directory
```

### Integration Tests
1. Compare context collection quality before/after improvements
2. Measure relevance scores for known good/bad matches
3. Track token efficiency and collection speed

### A/B Testing
1. Run both old and new scoring in parallel
2. Compare agent success rates with each approach
3. Gather feedback on context quality

## Success Metrics

### Quantitative
- **Relevance Accuracy**: >90% of collected items used by agents
- **Token Efficiency**: <5% wasted tokens on irrelevant content
- **Collection Speed**: <1s for typical tasks
- **Cache Hit Rate**: >60% for similar tasks

### Qualitative
- Agent feedback on context quality
- Reduced need for manual context adjustment
- Fewer missed critical files
- Better handling of cross-cutting concerns

## Risk Mitigation

### Performance Risks
- **Mitigation**: Cache computed scores, limit depth of import analysis
- **Monitoring**: Track collection time percentiles

### Accuracy Risks  
- **Mitigation**: Gradual rollout with fallback to old scoring
- **Validation**: Manual review of scoring changes

### Complexity Risks
- **Mitigation**: Well-documented scoring components
- **Testing**: Comprehensive test suite for each component

## Conclusion

These improvements will significantly enhance the Context Manager's ability to provide relevant, focused context to agents. By moving from static scoring to dynamic, relationship-aware relevance calculation, we can better support the complex tasks that agents need to perform. The phased implementation approach ensures we can deliver value quickly while building toward a more sophisticated system.