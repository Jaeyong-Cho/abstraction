"""Tests for call graph module."""

import pytest
from core.call_graph import (
    CallGraph,
    CallGraphNode,
    build_call_graph,
    find_entry_points,
    get_abstraction_depth
)
from core.parser import FunctionInfo


def test_call_graph_initialization():
    """
    Test call graph initialization.
    
    Preconditions: none
    Postconditions: empty graph created
    """
    graph = CallGraph()
    
    assert len(graph.nodes) == 0
    assert len(graph.graph) == 0


def test_add_function_to_graph():
    """
    Test adding function to graph.
    
    Preconditions: valid function info provided
    Postconditions: function added as node
    """
    graph = CallGraph()
    func_info = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=5,
        body="def test_func(): pass",
        calls=[],
        code_hash="abc"
    )
    
    graph.add_function(func_info)
    
    assert "test_func" in graph.nodes
    assert len(graph.nodes) == 1


def test_build_call_graph_basic():
    """
    Test building call graph from functions.
    
    Preconditions: list of functions with calls
    Postconditions: graph built with edges
    """
    func1 = FunctionInfo(
        name="main",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def main(): helper()",
        calls=["helper"],
        code_hash="abc1"
    )
    
    func2 = FunctionInfo(
        name="helper",
        file_path="test.py",
        line_number=5,
        end_line_number=7,
        body="def helper(): pass",
        calls=[],
        code_hash="abc2"
    )
    
    graph = build_call_graph([func1, func2])
    
    assert len(graph.nodes) == 2
    assert "helper" in graph.nodes["main"].callees


def test_find_entry_points_single():
    """
    Test finding entry point.
    
    Preconditions: graph with one entry point
    Postconditions: entry point identified
    """
    func1 = FunctionInfo(
        name="main",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def main(): helper()",
        calls=["helper"],
        code_hash="abc1"
    )
    
    func2 = FunctionInfo(
        name="helper",
        file_path="test.py",
        line_number=5,
        end_line_number=7,
        body="def helper(): pass",
        calls=[],
        code_hash="abc2"
    )
    
    graph = build_call_graph([func1, func2])
    entry_points = find_entry_points(graph)
    
    assert len(entry_points) == 1
    assert "main" in entry_points


def test_abstraction_depth_entry_point():
    """
    Test abstraction depth for entry point.
    
    Preconditions: entry point function in graph
    Postconditions: depth is 0
    """
    func = FunctionInfo(
        name="main",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def main(): pass",
        calls=[],
        code_hash="abc"
    )
    
    graph = build_call_graph([func])
    depth = get_abstraction_depth(graph, "main")
    
    assert depth == 0


def test_call_graph_node_creation():
    """
    Test call graph node creation.
    
    Preconditions: valid parameters provided
    Postconditions: node created with correct attributes
    """
    node = CallGraphNode(
        function_name="test_func",
        file_path="test.py",
        line_number=10
    )
    
    assert node.function_name == "test_func"
    assert node.line_number == 10
    assert len(node.callers) == 0
    assert len(node.callees) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
