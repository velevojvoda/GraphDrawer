from datetime import date

import pytest

from graph_api import Edge, Graph, Node
from graph_platform import search


@pytest.fixture
def graph():
    g = Graph()
    g.add_node(Node("1", {"Name": "Anja", "Age": 25, "Height": 160.5, "Born": date(2000, 5, 1)}))
    g.add_node(Node("2", {"Name": "Nina", "Age": 30, "Height": 175.0}))
    g.add_node(Node("3", {"Name": "Filip", "Age": 15}))
    g.add_node(Node("4", {"Name": "Tanja", "City": "Novi Sad"}))
    g.add_edge(Edge("e1", "1", "2"))
    g.add_edge(Edge("e2", "2", "3"))
    g.add_edge(Edge("e3", "3", "1"))
    g.add_edge(Edge("e4", "1", "4"))
    return g


def ids(items):
    return [x.id for x in items]


def test_search_matches_attribute_value(graph):
    assert ids(search(graph, "Nina").nodes) == ["2"]


def test_search_matches_part_of_value(graph):
    assert ids(search(graph, "anj").nodes) == ["1", "4"]


def test_search_matches_attribute_name(graph):
    assert ids(search(graph, "born").nodes) == ["1"]


def test_search_ignores_case(graph):
    assert ids(search(graph, "ANJA").nodes) == ids(search(graph, "anja").nodes)


def test_search_matches_numbers_and_dates(graph):
    assert ids(search(graph, "25").nodes) == ["1"]
    assert ids(search(graph, "160.5").nodes) == ["1"]
    assert ids(search(graph, "2000-05").nodes) == ["1"]


def test_search_without_match_returns_empty_graph(graph):
    result = search(graph, "xyz")
    assert result.nodes == [] and result.edges == []


@pytest.mark.parametrize("query", ["", "   "])
def test_empty_search_keeps_whole_graph(graph, query):
    result = search(graph, query)
    assert ids(result.nodes) == ids(graph.nodes)
    assert ids(result.edges) == ids(graph.edges)


def test_search_keeps_only_edges_between_matching_nodes(graph):
    assert ids(search(graph, "anj").edges) == ["e4"]


def test_search_does_not_change_original_graph(graph):
    search(graph, "Filip")
    assert len(graph.nodes) == 4 and len(graph.edges) == 4


def test_search_can_be_chained(graph):
    result = search(search(graph, "anj"), "novi")
    assert ids(result.nodes) == ["4"]