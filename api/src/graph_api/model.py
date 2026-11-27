"""Graph data model shared by the platform and all plugins."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Union

class GraphError(Exception):
    """Base class for all errors raised by the graph model."""


class DuplicateIdError(GraphError):
    """Raised when a node or an edge with the same id already exists."""


class NodeNotFoundError(GraphError):
    """Raised when a node with the given id does not exist."""


class EdgeNotFoundError(GraphError):
    """Raised when an edge with the given id does not exist."""


class NodeHasEdgesError(GraphError):
    """Raised when deleting a node that is still connected to edges."""

AttributeValue = Union[int, float, str, date]

__ALLOWED_TYPES = (int, float, str, date)

def _check_attributes(attributes: dict[str, AttributeValue]):
    """Raise TypeError if any attribute value is not an allowed type."""
    for name, value in attributes.items():
        if not isinstance(value, __ALLOWED_TYPES):
            raise TypeError(f"Attribute '{name}' has unsupported type {type(value).__name__}; "
                f"allowed types are int, float, str and date")

@dataclass
class Node:
    """A graph node with a unique id and typed attributes.

    Example: Node("1", {"Name": "Alice", "Age": 25})

    Raises TypeError if an attribute value is not int, float, str or date. """
    id: str
    attributes: dict[str, AttributeValue] = field(default_factory=dict)

    def __post_init__(self):
        _check_attributes(self.attributes)


@dataclass
class Edge:
    """A connection between two nodes, given by their ids.

    In a directed graph the edge goes from source to target.
    In an undirected graph the order does not matter.

    Example: Edge("e1", "1", "2", {"Name": "Siblings"})

    Raises TypeError if an attribute value is not int, float, str or date."""

    id: str
    source: str
    target: str
    attributes: dict[str, AttributeValue] = field(default_factory=dict)

    def __post_init__(self):
        _check_attributes(self.attributes)


class Graph:
    """A directed or undirected graph of class: Node and class: Edge objects.

    Cycles, self-loops and disconnected parts are allowed. Node and edge ids
    must be unique, and every edge must connect two existing nodes. """

    def __init__(self, directed: bool = True):
        """Create an empty graph.

        Param directed: True for a directed graph, False for an undirected one. """
        self.directed = directed
        self._nodes: dict[str, Node] = {}
        self._edges: dict[str, Edge] = {}

    @property
    def nodes(self):
        """All nodes, in the order they were added (a copy of the list)."""
        return list(self._nodes.values())

    @property
    def edges(self):
        """All edges, in the order they were added (a copy of the list)."""
        return list(self._edges.values())

    def has_node(self, node_id: str):
        """Return True if a node with node_id exists."""
        return node_id in self._nodes

    def get_node(self, node_id: str):
        """Return the node with node_id.

        Raises NodeNotFoundError if there is no such node."""
        try:
            return self._nodes[node_id]
        except KeyError:
            raise NodeNotFoundError(f"Node {node_id} does not exist.") from None

    def get_edge(self, edge_id: str):
        """Return the edge with edge_id.

        Raises EdgeNotFoundError if there is no such edge. """
        try:
            return self._edges[edge_id]
        except KeyError:
            raise EdgeNotFoundError(f"Edge {edge_id} does not exist.") from None

    def edges_of(self, node_id: str):
        """Return all edges that start or end in the node.

        Raises NodeNotFoundError if there is no such node. """
        self.get_node(node_id)
        return [e for e in self._edges.values() if node_id in (e.source, e.target)]

    def neighbors(self, node_id: str):
        """Return the nodes reachable from node_id by one edge.

        In a directed graph only outgoing edges are followed.
        In an undirected graph edges are followed in both directions.

        Raises NodeNotFoundError if there is no such node. """
        self.get_node(node_id)
        result = []
        for edge in self._edges.values():
            if edge.source == node_id:
                result.append(self._nodes[edge.target])
            elif not self.directed and edge.target == node_id:
                result.append(self._nodes[edge.source])
        return result

    def add_node(self, node: Node):
        """Add a node to the graph and return it.

        Raises DuplicateIdError if a node with the same id already exists."""
        if node.id in self._nodes:
            raise DuplicateIdError(f"Node {node.id} already exists.")
        self._nodes[node.id] = node
        return node

    def add_edge(self, edge: Edge):
        """Add an edge between two existing nodes and return it.

        Raises DuplicateIdError if an edge with the same id already exists.
        Raises NodeNotFoundError if the source or target node does not exist. """
        if edge.id in self._edges:
            raise DuplicateIdError(f"Edge {edge.id} already exists.")
        self.get_node(edge.source)
        self.get_node(edge.target)
        self._edges[edge.id] = edge
        return edge

    def update_node(self, node_id: str, attributes: dict[str, AttributeValue]) -> Node:
        """Add or overwrite the given attributes of a node and return it.

        Attributes that are not given stay unchanged.

        Raises NodeNotFoundError if there is no such node.
        Raises TypeError if a value is not int, float, str or date. """
        _check_attributes(attributes)
        node = self.get_node(node_id)
        node.attributes.update(attributes)
        return node

    def update_edge(self, edge_id: str, attributes: dict[str, AttributeValue]) -> Edge:
        """Add or overwrite the given attributes of an edge and return it.

        Attributes that are not given stay unchanged.

        Raises EdgeNotFoundError if there is no such edge.
        Raises TypeError if a value is not int, float, str or date."""
        _check_attributes(attributes)
        edge = self.get_edge(edge_id)
        edge.attributes.update(attributes)
        return edge

    def remove_edge(self, edge_id: str) -> Edge:
        """Remove an edge and return it.

        Raises EdgeNotFoundError if there is no such edge. """
        edge = self.get_edge(edge_id)
        del self._edges[edge_id]
        return edge

    def remove_node(self, node_id: str) -> Node:
        """Remove a node that has no edges and return it.

        A connected node cannot be removed; its edges must be removed first.

        Raises NodeNotFoundError if there is no such node.
        Raises NodeHasEdgesError if the node still has edges. """
        connected = self.edges_of(node_id)
        if connected:
            ids = ", ".join(e.id for e in connected)
            raise NodeHasEdgesError(
                f"Node {node_id} still has edges ({ids}); remove them first"
            )
        return self._nodes.pop(node_id)

    def clear(self):
        """Remove all nodes and edges from the graph."""
        self._nodes.clear()
        self._edges.clear()

    def subgraph(self, node_ids: Iterable[str]):
        """Return a new graph with the given nodes and only the edges between them.

        Used by search and filter. The original graph is not changed, and ids
        that do not exist are ignored. The subgraph shares the same node and
        edge objects, so changing an attribute in one is visible in the other.
        """
        ids = set(node_ids)
        sub = Graph(directed=self.directed)
        for node in self._nodes.values():
            if node.id in ids:
                sub.add_node(node)
        for edge in self._edges.values():
            if edge.source in ids and edge.target in ids:
                sub.add_edge(edge)
        return sub