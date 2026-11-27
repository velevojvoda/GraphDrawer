from datetime import date

import pytest

from graph_api import (
    DuplicateIdError, Edge, EdgeNotFoundError, Graph, Node,
    NodeHasEdgesError, NodeNotFoundError,
)


def make_graph(directed=True):
    """Graph with a cycle: 1 -> 2 -> 3 -> 1."""
    g = Graph(directed=directed)
    g.add_node(Node("1", {"Name": "Anja", "Age": 21, "Height": 165.5, "Born": date(2005, 9, 21)}))
    g.add_node(Node("2", {"Name": "Filip", "Age": 30}))
    g.add_node(Node("3", {"Name": "Nina", "Age": 15}))
    g.add_edge(Edge("e1", "1", "2"))
    g.add_edge(Edge("e2", "2", "3"))
    g.add_edge(Edge("e3", "3", "1"))
    return g


def ids(items):
    return [x.id for x in items]


def test_values_keep_type():
    a = make_graph().get_node("1").attributes
    assert type(a["Age"]) is int and type(a["Height"]) is float and type(a["Born"]) is date


def test_unsupported_type_rejected():
    with pytest.raises(TypeError):
        Node("x", {"Tags": ["a"]})
    with pytest.raises(TypeError):
        make_graph().update_node("1", {"Tags": ["a"]})


def test_duplicates():
    g = make_graph()
    with pytest.raises(DuplicateIdError):
        g.add_node(Node("1"))
    with pytest.raises(DuplicateIdError):
        g.add_edge(Edge("e1", "1", "3"))


def test_edge_to_missing_node():
    with pytest.raises(NodeNotFoundError):
        make_graph().add_edge(Edge("e9", "1", "99"))


def test_both_directions_and_self_loop():
    g = make_graph()
    g.add_edge(Edge("e4", "2", "1"))
    g.add_edge(Edge("e5", "1", "1"))
    assert len(g.edges) == 5


def test_neighbors_directed_and_undirected():
    assert ids(make_graph(True).neighbors("1")) == ["2"]
    assert sorted(ids(make_graph(False).neighbors("1"))) == ["2", "3"]


def test_update():
    g = make_graph()
    g.update_node("2", {"Age": 40, "City": "Novi Sad"})
    assert g.get_node("2").attributes == {"Name": "Filip", "Age": 40, "City": "Novi Sad"}
    g.update_edge("e1", {"Name": "Siblings"})
    assert g.get_edge("e1").attributes == {"Name": "Siblings"}


def test_remove_node_with_edges_fails_then_works():
    g = make_graph()
    with pytest.raises(NodeHasEdgesError):
        g.remove_node("1")
    g.remove_edge("e1")
    g.remove_edge("e3")
    g.remove_node("1")
    assert ids(g.nodes) == ["2", "3"]
    with pytest.raises(EdgeNotFoundError):
        g.remove_edge("e1")


def test_subgraph():
    g = make_graph()
    sub = g.subgraph(["1", "2", "missing"])
    assert ids(sub.nodes) == ["1", "2"]
    assert ids(sub.edges) == ["e1"]
    assert sub.directed is True
    assert len(g.nodes) == 3 and len(g.edges) == 3


def test_clear():
    g = make_graph()
    g.clear()
    assert g.nodes == [] and g.edges == []