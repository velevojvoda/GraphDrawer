"""Search and filter operations over a graph.

Every operation returns a new subgraph and never changes the given graph,
so operations can be chained: ``search(filter_graph(g, "Age > 20"), "ali")``.
"""

from __future__ import annotations
from graph_api import Graph, Node

def search(graph: Graph, query: str):
    """Return a subgraph with the nodes that match a free-text query.

    A node matches if the query is contained in the name or in the value of
    any of its attributes. The comparison ignores letter case, and values that
    are not strings (int, float, date) are compared by their text form.

    Only edges between the matching nodes are kept. An empty query (or one
    with only spaces) keeps all nodes.

    :param graph: The graph to search. It is not changed.
    :param query: The text to look for.
    :return: A new graph with the matching nodes and the edges between them. """

    text = query.strip().lower()
    if not text:
        return graph.subgraph(node.id for node in graph.nodes)
    return graph.subgraph(
        node.id for node in graph.nodes if _node_contains(node, text)
    )

def _node_contains(node: Node, text: str):
    """Return True if text is in any attribute name or value of the node.

    Text must already be in lower case. """
    return any(
        text in name.lower() or text in str(value).lower()
        for name, value in node.attributes.items()
    )