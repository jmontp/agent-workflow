# Graph-Based Librarian Migration Plan

## Executive Summary

This plan outlines the migration from Context Manager v1/v2's monolithic architecture to a graph-based librarian model. The new system transforms context management from file-based storage with pattern matching to a knowledge graph with active curation capabilities.

## Vision: The Graph Librarian

### Core Metaphor
Instead of a "manager" that stores and retrieves, we have a "librarian" that:
- **Curates** knowledge into a navigable graph structure
- **Understands** relationships between concepts, not just keywords
- **Guides** users through the knowledge space
- **Learns** optimal organization from usage patterns
- **Maintains** the health and relevance of the collection

### Architecture Shift
```
Current: Monolithic File Store → New: Distributed Knowledge Graph

Before:                          After:
┌─────────────────┐             ┌──────────────────┐
│ Context Manager │             │ Graph Librarian  │
├─────────────────┤             ├──────────────────┤
│ - File storage  │             │ - Node store     │
│ - Pattern match │  ────→      │ - Edge traversal │
│ - Linear search │             │ - Graph queries  │
│ - Static index  │             │ - Living graph   │
└─────────────────┘             └──────────────────┘
```

## What to Keep from Current Implementation

### 1. Core Concepts (Preserve & Enhance)
- **Context Types** → Node types in graph
- **Project Index** → Graph metadata layer
- **Task Analysis** → Query intent understanding
- **Semantic Understanding** → Edge relationship types

### 2. Valuable Features (Migrate)
- CLI interface (cm.py)
- Web UI components
- Documentation gateway concept
- Pattern detection algorithms
- Claude integration for analysis

### 3. Data Structures (Transform)
```python
# Current
@dataclass
class Context:
    id: str
    type: ContextType
    data: Dict[str, Any]
    relationships: List[str]  # Simple ID references

# New Graph Model
@dataclass
class ContextNode:
    id: str
    type: NodeType
    data: Dict[str, Any]
    embeddings: Optional[np.ndarray]  # For semantic search
    
@dataclass
class ContextEdge:
    source_id: str
    target_id: str
    relationship_type: RelationType
    weight: float  # Strength of relationship
    metadata: Dict[str, Any]
```

## What to Completely Redesign

### 1. Storage Layer
**Current**: JSON files in dated folders
**New**: Graph database with multiple backends
```python
# Pluggable storage backends
class GraphStorage(ABC):
    @abstractmethod
    def add_node(self, node: ContextNode) -> None: ...
    
    @abstractmethod
    def add_edge(self, edge: ContextEdge) -> None: ...
    
    @abstractmethod
    def traverse(self, start_node: str, relationship: RelationType) -> List[ContextNode]: ...

# Implementations
class InMemoryGraph(GraphStorage): ...  # For development
class Neo4jGraph(GraphStorage): ...     # For production
class RedisGraph(GraphStorage): ...     # For caching
```

### 2. Query System
**Current**: Keyword matching + file scanning
**New**: Graph traversal + semantic similarity
```python
# Graph Query Language
class GraphQuery:
    """
    Example: "Find all decisions related to authentication 
              that led to code changes in the last week"
    """
    def __init__(self, natural_language: str):
        self.intent = self._parse_intent(natural_language)
        self.constraints = self._extract_constraints(natural_language)
        self.traversal_hints = self._optimize_path(self.intent)
```

### 3. Indexing Strategy
**Current**: Rebuild entire index periodically
**New**: Incremental graph updates with automatic relationship discovery
```python
class GraphIndexer:
    def on_node_added(self, node: ContextNode):
        # Automatically discover relationships
        related_nodes = self._find_semantic_neighbors(node)
        for related in related_nodes:
            edge = self._compute_relationship(node, related)
            self.graph.add_edge(edge)
```

## Migration Path for Existing Contexts

### Phase 1: Dual Mode Operation (Week 1)
1. **Add graph layer alongside existing system**
   ```python
   class HybridContextManager(ContextManager):
       def __init__(self):
           super().__init__()
           self.graph = GraphLibrarian()
       
       def store(self, context: Context):
           # Store in both systems
           super().store(context)
           self.graph.add_node(self._context_to_node(context))
   ```

2. **Build migration tools**
   ```python
   # scripts/migrate_to_graph.py
   def migrate_contexts(start_date: date, end_date: date):
       contexts = load_contexts_in_range(start_date, end_date)
       graph = GraphLibrarian()
       
       # First pass: Create nodes
       for context in contexts:
           node = transform_context_to_node(context)
           graph.add_node(node)
       
       # Second pass: Discover relationships
       graph.build_relationships(algorithm='semantic_similarity')
   ```

### Phase 2: Graph-First with Fallback (Week 2-3)
1. **Route queries through graph first**
2. **Fall back to file search if needed**
3. **Measure performance differences**
4. **Gather usage patterns**

### Phase 3: Complete Migration (Week 4)
1. **Archive file-based storage**
2. **Switch fully to graph backend**
3. **Update all interfaces**

## Incremental Rollout Strategy

### Week 1: Foundation
- [ ] Create graph storage interface
- [ ] Implement in-memory graph backend
- [ ] Add graph layer to existing CM
- [ ] Build context-to-node transformer
- [ ] Create basic graph queries

### Week 2: Intelligence Layer
- [ ] Implement semantic similarity edges
- [ ] Add relationship discovery
- [ ] Create graph traversal algorithms
- [ ] Build query intent parser
- [ ] Add graph visualization API

### Week 3: Integration
- [ ] Update CLI to use graph queries
- [ ] Modify web UI for graph visualization
- [ ] Implement caching layer
- [ ] Add performance monitoring
- [ ] Create migration tools

### Week 4: Optimization
- [ ] Tune graph algorithms
- [ ] Implement graph pruning
- [ ] Add predictive pre-fetching
- [ ] Create backup/restore tools
- [ ] Complete migration

## Testing Approach

### 1. Unit Tests
```python
def test_graph_storage():
    graph = InMemoryGraph()
    node = ContextNode(id="test", type=NodeType.DECISION, data={})
    graph.add_node(node)
    assert graph.get_node("test") == node

def test_relationship_discovery():
    indexer = GraphIndexer()
    node1 = create_test_node("authentication decision")
    node2 = create_test_node("security code change")
    edges = indexer.discover_relationships(node1, node2)
    assert any(e.relationship_type == RelationType.INFLUENCES for e in edges)
```

### 2. Integration Tests
- Test dual-mode operation
- Verify migration tools
- Check query equivalence
- Measure performance

### 3. A/B Testing
- Run both systems in parallel
- Compare result quality
- Measure query performance
- Track user satisfaction

## Performance Benchmarks

### Target Metrics
| Operation | Current (File-based) | Target (Graph-based) |
|-----------|---------------------|---------------------|
| Store Context | 50ms | 10ms |
| Simple Query | 200ms | 20ms |
| Complex Query | 2000ms | 100ms |
| Relationship Discovery | N/A | 50ms/node |
| Graph Traversal (3 hops) | N/A | 10ms |

### Measurement Tools
```python
@benchmark
def measure_query_performance():
    query = "Find all decisions about caching"
    
    # Current system
    start = time.time()
    old_results = context_manager.query(query)
    old_time = time.time() - start
    
    # Graph system
    start = time.time()
    new_results = graph_librarian.query(query)
    new_time = time.time() - start
    
    return {
        'old_time': old_time,
        'new_time': new_time,
        'speedup': old_time / new_time,
        'result_quality': compare_results(old_results, new_results)
    }
```

## Success Metrics

### Technical Success
1. **Performance**: 10x faster complex queries
2. **Scalability**: Handle 1M+ nodes efficiently
3. **Accuracy**: 95%+ relevant results in top 10
4. **Reliability**: 99.9% uptime with automatic recovery

### User Success
1. **Discovery**: Find unexpected connections
2. **Navigation**: Explore knowledge naturally
3. **Understanding**: Visualize project structure
4. **Efficiency**: Reduce time to find information by 80%

### Business Success
1. **Adoption**: 100% of agents using graph queries
2. **Quality**: 50% reduction in redundant documentation
3. **Learning**: System improves with usage
4. **Insights**: Generate weekly project intelligence reports

## Implementation Roadmap

### Immediate Actions (Day 1-2)
1. Create `graph_librarian/` package structure
2. Define core interfaces (GraphStorage, GraphQuery)
3. Implement in-memory backend
4. Write initial test suite

### Week 1 Deliverables
1. Working graph storage with basic operations
2. Context-to-node migration tool
3. Simple graph queries (by type, by relationship)
4. Performance benchmark suite

### Week 2 Deliverables
1. Semantic similarity edges
2. Query intent parser
3. Graph visualization API
4. Dual-mode operation

### Week 3 Deliverables
1. Complete CLI integration
2. Web UI graph explorer
3. Migration tools tested
4. Performance optimization

### Week 4 Deliverables
1. Full production deployment
2. Monitoring and alerting
3. Documentation and training
4. Post-migration analysis

## Risk Mitigation

### Technical Risks
1. **Graph complexity**: Start simple, add features incrementally
2. **Performance regression**: Maintain dual-mode as fallback
3. **Data loss**: Implement robust backup/restore
4. **Integration issues**: Comprehensive testing at each phase

### Operational Risks
1. **User confusion**: Provide clear migration guides
2. **Feature parity**: Ensure all v2 features work in graph mode
3. **Downtime**: Use blue-green deployment
4. **Rollback**: Keep file-based system for 30 days

## Conclusion

The migration to a graph-based librarian model represents a fundamental shift in how we think about context management. Instead of managing files, we're curating knowledge. Instead of searching, we're exploring. Instead of storing, we're connecting.

This migration plan provides a safe, incremental path from the current system to a more powerful, scalable, and intelligent future. By maintaining compatibility while building new capabilities, we can transform the Context Manager into a true Graph Librarian that actively helps build better software.

### Next Steps
1. Review and approve this migration plan
2. Set up graph_librarian package structure
3. Begin Week 1 implementation
4. Schedule daily progress reviews

### Success Vision
In 4 weeks, we'll have transformed context management from a passive file store into an active knowledge graph that understands, connects, and guides. The Graph Librarian will not just store information—it will help us think.