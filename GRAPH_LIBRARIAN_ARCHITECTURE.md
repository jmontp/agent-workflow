# Graph Librarian Architecture Specification

## Core Architecture

### 1. Node Types and Schema

```python
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np
from datetime import datetime

class NodeType(Enum):
    # Primary node types
    CONTEXT = auto()      # Base context events
    DOCUMENT = auto()     # Documentation files
    CODE = auto()         # Code files/functions/classes
    DECISION = auto()     # Architectural decisions
    TASK = auto()         # Work items and tasks
    CONCEPT = auto()      # Abstract concepts/topics
    AGENT = auto()        # Agent entities
    PATTERN = auto()      # Detected patterns
    
    # Meta node types
    CLUSTER = auto()      # Group of related nodes
    TIMELINE = auto()     # Temporal sequence
    WORKFLOW = auto()     # Process flow

class RelationType(Enum):
    # Structural relationships
    CONTAINS = auto()         # Parent-child
    REFERENCES = auto()       # Direct reference
    IMPORTS = auto()          # Code dependency
    EXTENDS = auto()          # Inheritance/extension
    
    # Semantic relationships
    RELATES_TO = auto()       # General association
    EXPLAINS = auto()         # Documentation relationship
    IMPLEMENTS = auto()       # Code implements concept
    CONTRADICTS = auto()      # Conflicting information
    UPDATES = auto()          # Newer version
    
    # Temporal relationships
    PRECEDES = auto()         # Time-based ordering
    CAUSES = auto()           # Causal relationship
    ENABLES = auto()          # Prerequisite
    
    # Agent relationships
    CREATED_BY = auto()       # Authorship
    MODIFIED_BY = auto()      # Edit tracking
    REVIEWED_BY = auto()      # Quality control
    
    # Strength modifiers (used as edge properties)
    STRONG = auto()           # High confidence/relevance
    MODERATE = auto()         # Medium confidence
    WEAK = auto()             # Low confidence
    INFERRED = auto()         # System-generated

@dataclass
class ContextNode:
    """Base node structure for the knowledge graph"""
    # Identity
    id: str                          # Unique identifier
    type: NodeType                   # Node classification
    
    # Content
    title: str                       # Human-readable name
    summary: str                     # Brief description
    data: Dict[str, Any]            # Full content/metadata
    
    # Semantic features
    embeddings: Optional[np.ndarray] # Vector representation
    keywords: List[str]              # Extracted key terms
    importance: float                # 0.0-1.0 relevance score
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    source: str                      # Which agent/system created
    version: int                     # Version number
    tags: List[str]                  # User-defined categories
    
    # Graph properties
    in_degree: int = 0               # Number of incoming edges
    out_degree: int = 0              # Number of outgoing edges
    centrality: float = 0.0          # Network importance

@dataclass
class ContextEdge:
    """Relationship between nodes"""
    # Identity
    id: str
    source_id: str
    target_id: str
    
    # Relationship
    type: RelationType
    weight: float                    # Strength (0.0-1.0)
    confidence: float                # Certainty (0.0-1.0)
    
    # Metadata
    created_at: datetime
    source: str                      # Who/what created edge
    evidence: List[str]              # Why this edge exists
    properties: Dict[str, Any]       # Additional attributes
```

### 2. Graph Storage Interface

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple, Set

class GraphStorage(ABC):
    """Abstract interface for graph storage backends"""
    
    @abstractmethod
    def add_node(self, node: ContextNode) -> bool:
        """Add a node to the graph"""
        pass
    
    @abstractmethod
    def add_edge(self, edge: ContextEdge) -> bool:
        """Add an edge to the graph"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[ContextNode]:
        """Retrieve a node by ID"""
        pass
    
    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[ContextEdge]:
        """Retrieve an edge by ID"""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str, 
                     relationship: Optional[RelationType] = None,
                     direction: str = "both") -> List[ContextNode]:
        """Get neighboring nodes with optional filtering"""
        pass
    
    @abstractmethod
    def find_path(self, start_id: str, end_id: str, 
                  max_hops: int = 5) -> Optional[List[str]]:
        """Find shortest path between nodes"""
        pass
    
    @abstractmethod
    def search_nodes(self, query: Dict[str, Any]) -> List[ContextNode]:
        """Search nodes by properties"""
        pass
    
    @abstractmethod
    def traverse(self, start_id: str, 
                 traversal_spec: 'TraversalSpec') -> List[ContextNode]:
        """Complex graph traversal with custom logic"""
        pass

class InMemoryGraph(GraphStorage):
    """High-performance in-memory implementation"""
    
    def __init__(self):
        self.nodes: Dict[str, ContextNode] = {}
        self.edges: Dict[str, ContextEdge] = {}
        self.adjacency: Dict[str, Dict[str, List[str]]] = {}  # node -> {out: [], in: []}
        self.indices: Dict[str, Dict[Any, Set[str]]] = {}     # Property indices
        
    def add_node(self, node: ContextNode) -> bool:
        self.nodes[node.id] = node
        self.adjacency[node.id] = {"out": [], "in": []}
        self._update_indices(node)
        return True
    
    def add_edge(self, edge: ContextEdge) -> bool:
        self.edges[edge.id] = edge
        self.adjacency[edge.source_id]["out"].append(edge.id)
        self.adjacency[edge.target_id]["in"].append(edge.id)
        
        # Update node degrees
        self.nodes[edge.source_id].out_degree += 1
        self.nodes[edge.target_id].in_degree += 1
        
        return True
    
    def get_neighbors(self, node_id: str, 
                     relationship: Optional[RelationType] = None,
                     direction: str = "both") -> List[ContextNode]:
        neighbors = []
        
        if direction in ["out", "both"]:
            for edge_id in self.adjacency[node_id]["out"]:
                edge = self.edges[edge_id]
                if relationship is None or edge.type == relationship:
                    neighbors.append(self.nodes[edge.target_id])
        
        if direction in ["in", "both"]:
            for edge_id in self.adjacency[node_id]["in"]:
                edge = self.edges[edge_id]
                if relationship is None or edge.type == relationship:
                    neighbors.append(self.nodes[edge.source_id])
        
        return neighbors
```

### 3. Graph Query Engine

```python
@dataclass
class TraversalSpec:
    """Specification for graph traversal"""
    max_depth: int = 3
    relationship_types: Optional[List[RelationType]] = None
    node_filter: Optional[Callable[[ContextNode], bool]] = None
    edge_filter: Optional[Callable[[ContextEdge], bool]] = None
    visit_order: str = "breadth_first"  # or "depth_first"
    max_results: Optional[int] = None

class GraphQueryEngine:
    """Advanced query capabilities for the graph"""
    
    def __init__(self, storage: GraphStorage):
        self.storage = storage
        self.query_cache = {}
        
    def find_related_concepts(self, concept: str, 
                             max_distance: int = 2) -> List[Tuple[ContextNode, float]]:
        """Find concepts related to the given term"""
        # Start from concept nodes
        concept_nodes = self.storage.search_nodes({
            "type": NodeType.CONCEPT,
            "keywords": concept
        })
        
        related = []
        for node in concept_nodes:
            # Traverse outward
            traversal = TraversalSpec(
                max_depth=max_distance,
                relationship_types=[RelationType.RELATES_TO, 
                                  RelationType.IMPLEMENTS,
                                  RelationType.EXPLAINS]
            )
            neighbors = self.storage.traverse(node.id, traversal)
            
            for neighbor in neighbors:
                distance = self._calculate_semantic_distance(node, neighbor)
                related.append((neighbor, 1.0 - distance))
        
        # Sort by relevance
        related.sort(key=lambda x: x[1], reverse=True)
        return related
    
    def trace_decision_impact(self, decision_id: str) -> Dict[str, Any]:
        """Trace the impact of a decision through the graph"""
        decision_node = self.storage.get_node(decision_id)
        if not decision_node or decision_node.type != NodeType.DECISION:
            return {}
        
        impact = {
            "decision": decision_node,
            "direct_changes": [],
            "affected_components": [],
            "cascading_effects": []
        }
        
        # Find direct changes
        direct = self.storage.get_neighbors(
            decision_id, 
            RelationType.CAUSES,
            direction="out"
        )
        impact["direct_changes"] = direct
        
        # Find affected components through 2-hop traversal
        for change in direct:
            affected = self.storage.get_neighbors(
                change.id,
                RelationType.MODIFIES,
                direction="out"
            )
            impact["affected_components"].extend(affected)
        
        # Find cascading effects through pattern matching
        patterns = self._find_cascading_patterns(decision_id)
        impact["cascading_effects"] = patterns
        
        return impact
    
    def find_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """Identify areas lacking documentation or connections"""
        gaps = []
        
        # Find isolated nodes (low connectivity)
        all_nodes = self.storage.search_nodes({})
        for node in all_nodes:
            if node.in_degree + node.out_degree < 2:
                gaps.append({
                    "type": "isolated_node",
                    "node": node,
                    "suggestion": f"Connect {node.title} to related concepts"
                })
        
        # Find code without documentation
        code_nodes = self.storage.search_nodes({"type": NodeType.CODE})
        for code in code_nodes:
            docs = self.storage.get_neighbors(
                code.id,
                RelationType.EXPLAINS,
                direction="in"
            )
            if not docs:
                gaps.append({
                    "type": "undocumented_code",
                    "node": code,
                    "suggestion": f"Document {code.title}"
                })
        
        return gaps
```

### 4. Semantic Understanding Layer

```python
class SemanticAnalyzer:
    """Semantic analysis and embedding generation"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # In production, use actual embedding model
        self.embedding_dim = 384
        self.concept_extractor = ConceptExtractor()
        
    def generate_embeddings(self, text: str) -> np.ndarray:
        """Generate semantic embeddings for text"""
        # Placeholder - in production use actual model
        return np.random.randn(self.embedding_dim)
    
    def extract_concepts(self, node: ContextNode) -> List[str]:
        """Extract key concepts from node content"""
        text = f"{node.title} {node.summary} {' '.join(node.keywords)}"
        return self.concept_extractor.extract(text)
    
    def calculate_similarity(self, node1: ContextNode, 
                           node2: ContextNode) -> float:
        """Calculate semantic similarity between nodes"""
        if node1.embeddings is None or node2.embeddings is None:
            # Fallback to keyword similarity
            keywords1 = set(node1.keywords)
            keywords2 = set(node2.keywords)
            if not keywords1 or not keywords2:
                return 0.0
            intersection = keywords1.intersection(keywords2)
            union = keywords1.union(keywords2)
            return len(intersection) / len(union)
        
        # Cosine similarity
        dot_product = np.dot(node1.embeddings, node2.embeddings)
        norm1 = np.linalg.norm(node1.embeddings)
        norm2 = np.linalg.norm(node2.embeddings)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

class RelationshipDiscovery:
    """Automatically discover relationships between nodes"""
    
    def __init__(self, semantic_analyzer: SemanticAnalyzer):
        self.analyzer = semantic_analyzer
        self.patterns = self._load_relationship_patterns()
    
    def discover_relationships(self, node: ContextNode, 
                             graph: GraphStorage) -> List[ContextEdge]:
        """Find potential relationships for a new node"""
        discovered = []
        
        # Find semantically similar nodes
        candidates = self._find_similar_nodes(node, graph)
        
        for candidate, similarity in candidates:
            # Determine relationship type based on node types and content
            rel_type = self._infer_relationship_type(node, candidate)
            
            if rel_type:
                edge = ContextEdge(
                    id=f"{node.id}-{rel_type.value}-{candidate.id}",
                    source_id=node.id,
                    target_id=candidate.id,
                    type=rel_type,
                    weight=similarity,
                    confidence=similarity * 0.8,  # Adjust confidence
                    created_at=datetime.now(),
                    source="RelationshipDiscovery",
                    evidence=[f"Semantic similarity: {similarity:.2f}"],
                    properties={}
                )
                discovered.append(edge)
        
        return discovered
    
    def _infer_relationship_type(self, source: ContextNode, 
                                target: ContextNode) -> Optional[RelationType]:
        """Infer the most likely relationship type"""
        # Type-based rules
        type_rules = {
            (NodeType.CODE, NodeType.DOCUMENT): RelationType.EXPLAINS,
            (NodeType.DECISION, NodeType.CODE): RelationType.CAUSES,
            (NodeType.TASK, NodeType.CODE): RelationType.IMPLEMENTS,
            (NodeType.CONCEPT, NodeType.CODE): RelationType.IMPLEMENTS,
            (NodeType.DOCUMENT, NodeType.CONCEPT): RelationType.EXPLAINS,
        }
        
        rule_key = (source.type, target.type)
        if rule_key in type_rules:
            return type_rules[rule_key]
        
        # Content-based inference
        if "update" in source.title.lower() or "update" in target.title.lower():
            return RelationType.UPDATES
        
        if "import" in str(source.data) and target.type == NodeType.CODE:
            return RelationType.IMPORTS
        
        # Default to general relationship
        return RelationType.RELATES_TO
```

### 5. Graph Librarian Core

```python
class GraphLibrarian:
    """The main interface for the graph-based context system"""
    
    def __init__(self, storage: GraphStorage = None):
        self.storage = storage or InMemoryGraph()
        self.query_engine = GraphQueryEngine(self.storage)
        self.semantic_analyzer = SemanticAnalyzer()
        self.relationship_discovery = RelationshipDiscovery(self.semantic_analyzer)
        self.curation_rules = CurationRules()
        
    def add_context(self, context_data: Dict[str, Any]) -> ContextNode:
        """Add new context to the graph with automatic relationship discovery"""
        # Create node
        node = self._create_node_from_context(context_data)
        
        # Generate embeddings
        text_content = self._extract_text_content(context_data)
        node.embeddings = self.semantic_analyzer.generate_embeddings(text_content)
        
        # Extract concepts and keywords
        node.keywords = self.semantic_analyzer.extract_concepts(node)
        
        # Add to graph
        self.storage.add_node(node)
        
        # Discover and add relationships
        relationships = self.relationship_discovery.discover_relationships(
            node, self.storage
        )
        for edge in relationships:
            self.storage.add_edge(edge)
        
        # Update graph statistics
        self._update_graph_metrics()
        
        return node
    
    def query(self, natural_language: str) -> List[ContextNode]:
        """Query the graph using natural language"""
        # Parse query intent
        intent = self._parse_query_intent(natural_language)
        
        # Convert to graph traversal
        if intent["type"] == "find_related":
            return self.query_engine.find_related_concepts(
                intent["concept"],
                intent.get("max_distance", 2)
            )
        
        elif intent["type"] == "trace_impact":
            return self.query_engine.trace_decision_impact(
                intent["decision_id"]
            )
        
        elif intent["type"] == "find_by_properties":
            return self.storage.search_nodes(intent["properties"])
        
        else:
            # Fallback to semantic search
            return self._semantic_search(natural_language)
    
    def curate(self) -> Dict[str, Any]:
        """Perform curation tasks on the graph"""
        curation_report = {
            "timestamp": datetime.now(),
            "actions": []
        }
        
        # Find and merge duplicate nodes
        duplicates = self._find_duplicate_nodes()
        for dup_set in duplicates:
            merged = self._merge_nodes(dup_set)
            curation_report["actions"].append({
                "type": "merge_duplicates",
                "nodes": [n.id for n in dup_set],
                "result": merged.id
            })
        
        # Prune weak relationships
        weak_edges = self._find_weak_edges()
        for edge in weak_edges:
            if self._should_prune_edge(edge):
                self.storage.remove_edge(edge.id)
                curation_report["actions"].append({
                    "type": "prune_edge",
                    "edge": edge.id,
                    "reason": "Below relevance threshold"
                })
        
        # Identify knowledge gaps
        gaps = self.query_engine.find_knowledge_gaps()
        curation_report["knowledge_gaps"] = gaps
        
        # Update importance scores
        self._recalculate_importance_scores()
        
        return curation_report
    
    def visualize(self, focus_node_id: Optional[str] = None,
                  max_depth: int = 2) -> Dict[str, Any]:
        """Generate visualization data for the graph"""
        if focus_node_id:
            # Generate local neighborhood
            nodes, edges = self._get_neighborhood(focus_node_id, max_depth)
        else:
            # Generate overview
            nodes, edges = self._get_graph_overview()
        
        return {
            "nodes": [self._node_to_vis_format(n) for n in nodes],
            "edges": [self._edge_to_vis_format(e) for e in edges],
            "layout": "force-directed",
            "stats": self._get_graph_stats()
        }
```

### 6. Migration Tools

```python
class ContextMigrator:
    """Migrate from file-based to graph-based system"""
    
    def __init__(self, old_context_manager, graph_librarian):
        self.old_cm = old_context_manager
        self.graph = graph_librarian
        self.migration_log = []
        
    def migrate_contexts(self, start_date: datetime, 
                        end_date: datetime) -> Dict[str, Any]:
        """Migrate contexts within date range"""
        contexts = self.old_cm.get_contexts_in_range(start_date, end_date)
        
        results = {
            "total": len(contexts),
            "migrated": 0,
            "failed": 0,
            "relationships_created": 0
        }
        
        # Phase 1: Create all nodes
        node_map = {}  # old_id -> new_node
        for context in contexts:
            try:
                node = self._context_to_node(context)
                self.graph.storage.add_node(node)
                node_map[context.id] = node
                results["migrated"] += 1
            except Exception as e:
                self.migration_log.append({
                    "error": str(e),
                    "context_id": context.id
                })
                results["failed"] += 1
        
        # Phase 2: Create relationships
        for context in contexts:
            if context.id not in node_map:
                continue
                
            node = node_map[context.id]
            
            # Migrate explicit relationships
            for related_id in context.relationships:
                if related_id in node_map:
                    edge = ContextEdge(
                        id=f"{node.id}-relates-{related_id}",
                        source_id=node.id,
                        target_id=related_id,
                        type=RelationType.RELATES_TO,
                        weight=0.5,
                        confidence=1.0,
                        created_at=context.timestamp,
                        source="Migration",
                        evidence=["Explicit relationship in v1"],
                        properties={}
                    )
                    self.graph.storage.add_edge(edge)
                    results["relationships_created"] += 1
            
            # Discover new relationships
            discovered = self.graph.relationship_discovery.discover_relationships(
                node, self.graph.storage
            )
            for edge in discovered:
                self.graph.storage.add_edge(edge)
                results["relationships_created"] += 1
        
        return results
```

## Performance Optimizations

### 1. Caching Layer
```python
class GraphCache:
    """Multi-level caching for graph operations"""
    
    def __init__(self, redis_client=None):
        self.memory_cache = {}  # L1 cache
        self.redis = redis_client  # L2 cache
        self.cache_stats = {"hits": 0, "misses": 0}
        
    def get_cached_traversal(self, start_id: str, 
                           spec: TraversalSpec) -> Optional[List[ContextNode]]:
        """Check cache for traversal results"""
        cache_key = self._generate_cache_key(start_id, spec)
        
        # Check L1
        if cache_key in self.memory_cache:
            self.cache_stats["hits"] += 1
            return self.memory_cache[cache_key]
        
        # Check L2
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                self.cache_stats["hits"] += 1
                result = self._deserialize_nodes(cached)
                self.memory_cache[cache_key] = result
                return result
        
        self.cache_stats["misses"] += 1
        return None
```

### 2. Index Optimization
```python
class GraphIndices:
    """Specialized indices for fast graph operations"""
    
    def __init__(self):
        self.type_index = {}  # NodeType -> Set[node_id]
        self.keyword_index = {}  # keyword -> Set[node_id]
        self.temporal_index = {}  # date -> Set[node_id]
        self.embedding_index = None  # FAISS or similar
        
    def build_embedding_index(self, nodes: List[ContextNode]):
        """Build vector similarity index"""
        embeddings = []
        node_ids = []
        
        for node in nodes:
            if node.embeddings is not None:
                embeddings.append(node.embeddings)
                node_ids.append(node.id)
        
        # In production, use FAISS or similar
        # self.embedding_index = faiss.IndexFlatL2(embedding_dim)
        # self.embedding_index.add(np.array(embeddings))
```

## Monitoring and Analytics

```python
class GraphAnalytics:
    """Analytics and monitoring for the graph"""
    
    def __init__(self, graph: GraphLibrarian):
        self.graph = graph
        
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health metrics"""
        return {
            "graph_size": {
                "nodes": self.graph.storage.node_count(),
                "edges": self.graph.storage.edge_count(),
                "avg_degree": self.graph.storage.average_degree()
            },
            "coverage": {
                "documented_code": self._calculate_doc_coverage(),
                "connected_nodes": self._calculate_connectivity(),
                "semantic_density": self._calculate_semantic_density()
            },
            "quality": {
                "duplicate_nodes": len(self._find_duplicates()),
                "weak_edges": len(self._find_weak_edges()),
                "isolated_nodes": len(self._find_isolated_nodes())
            },
            "performance": {
                "avg_query_time": self._get_avg_query_time(),
                "cache_hit_rate": self._get_cache_hit_rate(),
                "traversal_efficiency": self._calculate_traversal_efficiency()
            }
        }
```

## Example Usage

```python
# Initialize the Graph Librarian
librarian = GraphLibrarian()

# Add a new decision context
decision = librarian.add_context({
    "type": "decision",
    "title": "Use graph database for context management",
    "summary": "Migrate from file-based to graph-based storage",
    "data": {
        "rationale": "Better relationship modeling and query performance",
        "alternatives_considered": ["NoSQL", "Relational DB"],
        "impact": "Major architectural change"
    },
    "tags": ["architecture", "storage", "performance"]
})

# Query for related concepts
related = librarian.query("What decisions affected our storage architecture?")

# Trace decision impact
impact = librarian.query_engine.trace_decision_impact(decision.id)

# Perform curation
curation_report = librarian.curate()

# Generate visualization
vis_data = librarian.visualize(focus_node_id=decision.id, max_depth=3)
```

## Conclusion

This architecture provides a solid foundation for the Graph Librarian system, with:
- Rich node and edge types for comprehensive knowledge modeling
- Flexible storage backend support
- Powerful query and traversal capabilities
- Automatic relationship discovery
- Active curation and maintenance
- Performance optimization through caching and indexing
- Comprehensive monitoring and analytics

The system is designed to scale from small projects to large enterprise codebases while maintaining query performance and knowledge quality.