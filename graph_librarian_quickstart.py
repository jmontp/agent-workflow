#!/usr/bin/env python3
"""
Graph Librarian Quick Start Implementation

This file provides a minimal working implementation of the Graph Librarian
to demonstrate the core concepts and allow immediate experimentation.

Usage:
    python graph_librarian_quickstart.py
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum, auto
import json
import uuid
from collections import defaultdict
import math


class NodeType(Enum):
    """Core node types for the graph"""
    CONTEXT = auto()
    DOCUMENT = auto()
    CODE = auto()
    DECISION = auto()
    CONCEPT = auto()


class RelationType(Enum):
    """Core relationship types"""
    RELATES_TO = auto()
    EXPLAINS = auto()
    IMPLEMENTS = auto()
    CAUSES = auto()
    REFERENCES = auto()


@dataclass
class ContextNode:
    """Simplified node structure"""
    id: str
    type: NodeType
    title: str
    summary: str
    data: Dict[str, Any]
    keywords: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    importance: float = 0.5


@dataclass
class ContextEdge:
    """Simplified edge structure"""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    weight: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)


class InMemoryGraph:
    """Simple in-memory graph implementation"""
    
    def __init__(self):
        self.nodes: Dict[str, ContextNode] = {}
        self.edges: Dict[str, ContextEdge] = {}
        self.adjacency: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: {"out": [], "in": []}
        )
    
    def add_node(self, node: ContextNode) -> bool:
        """Add a node to the graph"""
        self.nodes[node.id] = node
        return True
    
    def add_edge(self, edge: ContextEdge) -> bool:
        """Add an edge to the graph"""
        self.edges[edge.id] = edge
        self.adjacency[edge.source_id]["out"].append(edge.id)
        self.adjacency[edge.target_id]["in"].append(edge.id)
        return True
    
    def get_node(self, node_id: str) -> Optional[ContextNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, direction: str = "out") -> List[ContextNode]:
        """Get neighboring nodes"""
        neighbors = []
        edge_ids = self.adjacency[node_id][direction]
        
        for edge_id in edge_ids:
            edge = self.edges[edge_id]
            neighbor_id = edge.target_id if direction == "out" else edge.source_id
            if neighbor_id in self.nodes:
                neighbors.append(self.nodes[neighbor_id])
        
        return neighbors
    
    def search_nodes(self, query: Dict[str, Any]) -> List[ContextNode]:
        """Simple search implementation"""
        results = []
        
        for node in self.nodes.values():
            match = True
            
            # Type filter
            if "type" in query and node.type != query["type"]:
                match = False
            
            # Keyword filter
            if "keywords" in query:
                query_keywords = set(query["keywords"])
                node_keywords = set(node.keywords)
                if not query_keywords.intersection(node_keywords):
                    match = False
            
            # Title search
            if "title_contains" in query:
                if query["title_contains"].lower() not in node.title.lower():
                    match = False
            
            if match:
                results.append(node)
        
        return results


class SimpleSemanticAnalyzer:
    """Simplified semantic analysis"""
    
    def calculate_similarity(self, node1: ContextNode, node2: ContextNode) -> float:
        """Calculate similarity between nodes using keyword overlap"""
        if not node1.keywords or not node2.keywords:
            return 0.0
        
        set1 = set(node1.keywords)
        set2 = set(node2.keywords)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        # In production, use NLP libraries
        stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'to'}
        # Split on common delimiters and clean
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # Keep meaningful words
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        # Return unique keywords
        return list(dict.fromkeys(keywords))


class RelationshipDiscovery:
    """Discover relationships between nodes"""
    
    def __init__(self, analyzer: SimpleSemanticAnalyzer):
        self.analyzer = analyzer
    
    def discover_relationships(self, node: ContextNode, 
                             graph: InMemoryGraph,
                             threshold: float = 0.1) -> List[ContextEdge]:
        """Find potential relationships for a node"""
        discovered = []
        
        for other_id, other_node in graph.nodes.items():
            if other_id == node.id:
                continue
            
            similarity = self.analyzer.calculate_similarity(node, other_node)
            
            if similarity > threshold:
                # Infer relationship type based on node types
                rel_type = self._infer_relationship_type(node, other_node)
                
                edge = ContextEdge(
                    id=f"{node.id}-{rel_type.name}-{other_id}",
                    source_id=node.id,
                    target_id=other_id,
                    type=rel_type,
                    weight=similarity
                )
                discovered.append(edge)
        
        return discovered
    
    def _infer_relationship_type(self, source: ContextNode, 
                                target: ContextNode) -> RelationType:
        """Simple relationship type inference"""
        if source.type == NodeType.CODE and target.type == NodeType.DOCUMENT:
            return RelationType.EXPLAINS
        elif source.type == NodeType.DECISION and target.type == NodeType.CODE:
            return RelationType.CAUSES
        elif source.type == NodeType.CONCEPT and target.type == NodeType.CODE:
            return RelationType.IMPLEMENTS
        else:
            return RelationType.RELATES_TO


class GraphLibrarianLite:
    """Simplified Graph Librarian for quick start"""
    
    def __init__(self):
        self.graph = InMemoryGraph()
        self.analyzer = SimpleSemanticAnalyzer()
        self.discovery = RelationshipDiscovery(self.analyzer)
    
    def add_context(self, context_data: Dict[str, Any]) -> ContextNode:
        """Add new context to the graph"""
        # Create node
        node = ContextNode(
            id=str(uuid.uuid4()),
            type=NodeType[context_data.get("type", "CONTEXT").upper()],
            title=context_data.get("title", "Untitled"),
            summary=context_data.get("summary", ""),
            data=context_data.get("data", {}),
            keywords=self.analyzer.extract_keywords(
                f"{context_data.get('title', '')} {context_data.get('summary', '')}"
            )
        )
        
        # Add to graph
        self.graph.add_node(node)
        
        # Discover relationships
        relationships = self.discovery.discover_relationships(node, self.graph)
        for edge in relationships[:5]:  # Limit to top 5 relationships
            self.graph.add_edge(edge)
        
        print(f"Added node '{node.title}' with {len(relationships)} relationships")
        
        return node
    
    def query(self, natural_language: str) -> List[Dict[str, Any]]:
        """Simple query implementation"""
        # Extract keywords from query
        keywords = self.analyzer.extract_keywords(natural_language)
        
        # Search for nodes
        results = self.graph.search_nodes({"keywords": keywords})
        
        # Format results
        formatted_results = []
        for node in results:
            neighbors = self.graph.get_neighbors(node.id)
            formatted_results.append({
                "node": node,
                "connected_to": [n.title for n in neighbors]
            })
        
        return formatted_results
    
    def find_related(self, node_id: str, max_hops: int = 2) -> List[ContextNode]:
        """Find related nodes through graph traversal"""
        visited = set()
        to_visit = [(node_id, 0)]
        related = []
        
        while to_visit:
            current_id, distance = to_visit.pop(0)
            
            if current_id in visited or distance > max_hops:
                continue
            
            visited.add(current_id)
            
            if distance > 0:  # Don't include the starting node
                node = self.graph.get_node(current_id)
                if node:
                    related.append(node)
            
            # Add neighbors to visit
            neighbors = self.graph.get_neighbors(current_id)
            for neighbor in neighbors:
                if neighbor.id not in visited:
                    to_visit.append((neighbor.id, distance + 1))
        
        return related
    
    def visualize_graph(self) -> Dict[str, Any]:
        """Generate simple visualization data"""
        nodes = []
        edges = []
        
        for node in self.graph.nodes.values():
            nodes.append({
                "id": node.id,
                "label": node.title,
                "type": node.type.name,
                "size": len(self.graph.adjacency[node.id]["in"]) + 
                        len(self.graph.adjacency[node.id]["out"])
            })
        
        for edge in self.graph.edges.values():
            edges.append({
                "source": edge.source_id,
                "target": edge.target_id,
                "type": edge.type.name,
                "weight": edge.weight
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "avg_connections": len(edges) / len(nodes) if nodes else 0
            }
        }


def demo():
    """Demonstrate Graph Librarian capabilities"""
    print("🔮 Graph Librarian Quick Start Demo\n")
    
    # Initialize
    librarian = GraphLibrarianLite()
    
    # Add some sample contexts
    print("1️⃣ Adding contexts to the graph...\n")
    
    # Add a decision
    decision = librarian.add_context({
        "type": "decision",
        "title": "Implement caching strategy",
        "summary": "Use Redis cache for API response caching to improve performance",
        "data": {
            "rationale": "Current response times exceed 500ms",
            "expected_improvement": "80% reduction in response time"
        }
    })
    
    # Add related code
    code = librarian.add_context({
        "type": "code",
        "title": "cache.py implementation",
        "summary": "Redis cache wrapper implementation with TTL support",
        "data": {
            "file_path": "src/cache.py",
            "functions": ["get_cached", "set_cache", "invalidate"]
        }
    })
    
    # Add documentation
    doc = librarian.add_context({
        "type": "document",
        "title": "Caching Guide",
        "summary": "Documentation for Redis cache system usage and configuration",
        "data": {
            "file_path": "docs/CACHING.md",
            "sections": ["Overview", "Configuration", "Best Practices"]
        }
    })
    
    # Add a concept
    concept = librarian.add_context({
        "type": "concept",
        "title": "Performance Optimization",
        "summary": "Strategies for improving system performance including cache usage",
        "data": {
            "techniques": ["caching", "indexing", "query optimization"]
        }
    })
    
    print("\n2️⃣ Querying the graph...\n")
    
    # Natural language query
    results = librarian.query("How do we handle caching?")
    print(f"Query: 'How do we handle caching?'")
    print(f"Found {len(results)} results:")
    for result in results:
        print(f"  - {result['node'].title} (connected to: {', '.join(result['connected_to'])})")
    
    print("\n3️⃣ Finding related nodes...\n")
    
    # Find nodes related to the decision
    related = librarian.find_related(decision.id, max_hops=2)
    print(f"Nodes related to '{decision.title}':")
    for node in related:
        print(f"  - {node.title} ({node.type.name})")
    
    print("\n4️⃣ Graph statistics...\n")
    
    # Visualize
    viz_data = librarian.visualize_graph()
    stats = viz_data["stats"]
    print(f"Graph contains:")
    print(f"  - {stats['total_nodes']} nodes")
    print(f"  - {stats['total_edges']} edges")
    print(f"  - {stats['avg_connections']:.1f} average connections per node")
    
    print("\n✨ Demo complete! The graph is now queryable and will grow smarter with more data.")
    
    return librarian


if __name__ == "__main__":
    # Run the demo
    librarian = demo()
    
    print("\n\n💡 Try adding your own contexts:")
    print("librarian.add_context({")
    print("    'type': 'decision',")
    print("    'title': 'Your decision here',")
    print("    'summary': 'What and why',")
    print("    'data': {'any': 'additional data'}")
    print("})")