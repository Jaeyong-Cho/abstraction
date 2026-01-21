"""Call graph visualization."""

from typing import Optional, List, Set
import networkx as nx

from core.call_graph import CallGraph


def render_text_tree(
    graph: CallGraph,
    root: str,
    max_depth: int = 5
) -> str:
    """
    Render call graph as text tree.
    
    Preconditions: graph valid, root exists, max_depth positive
    Postconditions: returns formatted tree string
    """
    assert graph is not None, "Graph required"
    assert root in graph.nodes, "Root must exist in graph"
    assert max_depth > 0, "Max depth must be positive"
    
    lines = []
    visited: Set[str] = set()
    
    build_tree_lines(graph, root, 0, max_depth, lines, visited)
    
    result = '\n'.join(lines)
    
    assert isinstance(result, str), "Result must be string"
    return result


def build_tree_lines(
    graph: CallGraph,
    current: str,
    depth: int,
    max_depth: int,
    lines: List[str],
    visited: Set[str]
) -> None:
    """
    Recursively build tree lines.
    
    Preconditions: all parameters valid
    Postconditions: lines list populated with tree structure
    """
    if depth >= max_depth or current in visited:
        return
    
    visited.add(current)
    indent = "  " * depth
    marker = "- "
    
    node = graph.nodes.get(current)
    if not node:
        return
    
    display_name = extract_function_name_from_key(current)
    line = f"{indent}{marker}{display_name}"
    lines.append(line)
    
    for callee_key in sorted(node.callees):
        build_tree_lines(graph, callee_key, depth + 1, max_depth, lines, visited)


def extract_function_name_from_key(key: str) -> str:
    """
    Extract function name from function key.
    
    Preconditions: key has format 'path::name'
    Postconditions: returns function name portion
    """
    if "::" in key:
        return key.split("::")[-1]
    return key


def generate_dot_graph(graph: CallGraph, output_file: str) -> bool:
    """
    Generate DOT format graph file.
    
    Preconditions: graph valid, output_file is path
    Postconditions: DOT file written, returns success
    """
    assert graph is not None, "Graph required"
    assert output_file, "Output file required"
    
    try:
        import graphviz
        dot = graphviz.Digraph(comment='Call Graph')
        
        for key in graph.nodes:
            node = graph.nodes[key]
            display_name = extract_function_name_from_key(key)
            dot.node(key, display_name)
        
        for source_key in graph.nodes:
            node = graph.nodes[source_key]
            for target_key in node.callees:
                dot.edge(source_key, target_key)
        
        dot.render(output_file, format='png', cleanup=True)
        
        return True
        
    except ImportError:
        return False


def print_graph_statistics(graph: CallGraph) -> None:
    """
    Print graph statistics to stdout.
    
    Preconditions: graph is valid CallGraph
    Postconditions: statistics printed
    """
    assert graph is not None, "Graph required"
    
    node_count = len(graph.nodes)
    edge_count = graph.graph.number_of_edges()
    
    print(f"Total functions: {node_count}")
    print(f"Total calls: {edge_count}")
    
    if node_count > 0:
        avg_calls = edge_count / node_count
        print(f"Average calls per function: {avg_calls:.2f}")
    
    assert node_count >= 0, "Count must be non-negative"


def find_longest_path(graph: CallGraph, start: str) -> List[str]:
    """
    Find longest path from start node.
    
    Preconditions: graph valid, start exists
    Postconditions: returns longest path as node list
    """
    assert start in graph.nodes, "Start must exist"
    
    longest = [start]
    visited: Set[str] = set()
    
    explore_paths(graph, start, [start], visited, longest)
    
    assert len(longest) >= 1, "Path must contain at least start"
    return longest


def explore_paths(
    graph: CallGraph,
    current: str,
    path: List[str],
    visited: Set[str],
    longest: List[str]
) -> None:
    """
    Recursively explore paths to find longest.
    
    Preconditions: all parameters valid
    Postconditions: longest updated with longest found path
    """
    if len(path) > len(longest):
        longest.clear()
        longest.extend(path)
    
    visited.add(current)
    node = graph.nodes.get(current)
    
    if not node:
        visited.remove(current)
        return
    
    for callee in node.callees:
        if callee not in visited:
            path.append(callee)
            explore_paths(graph, callee, path, visited, longest)
            path.pop()
    
    visited.remove(current)
