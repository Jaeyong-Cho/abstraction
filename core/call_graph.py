"""Call graph construction and navigation."""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import networkx as nx

from .parser import FunctionInfo
from .contract import FunctionContract


def create_function_key(name: str, file_path: str) -> str:
    """
    Create unique key for function.
    
    Preconditions: name and file_path are non-empty
    Postconditions: returns unique identifier string
    """
    assert name, "Name required"
    assert file_path, "File path required"
    
    key = f"{file_path}::{name}"
    
    assert "::" in key, "Key must contain separator"
    return key


@dataclass
class CallGraphNode:
    """
    Node in the call graph representing a function.
    
    Preconditions: function_name is non-empty
    Postconditions: represents complete call graph node
    """
    function_name: str
    file_path: str
    line_number: int
    contract: Optional[FunctionContract] = None
    callers: Set[str] = field(default_factory=set)
    callees: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Validate node invariants."""
        assert self.function_name, "Function name required"
        assert self.line_number > 0, "Line number must be positive"


class CallGraph:
    """
    Directed call graph for navigating abstraction levels.
    
    Preconditions: initialized with valid function information
    Postconditions: provides navigable call graph structure
    """
    
    def __init__(self) -> None:
        """
        Initialize empty call graph.
        
        Preconditions: none
        Postconditions: empty graph ready for population
        """
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, CallGraphNode] = {}
        
        assert len(self.graph) == 0, "Graph must start empty"
    
    def add_function(self, func_info: FunctionInfo) -> None:
        """
        Add function to call graph.
        
        Preconditions: func_info is valid FunctionInfo
        Postconditions: function added as node in graph (duplicates overwritten)
        """
        assert func_info is not None, "Function info required"
        
        key = create_function_key(func_info.name, func_info.file_path)
        
        if key in self.nodes:
            existing_node = self.nodes[key]
            if existing_node.line_number != func_info.line_number:
                existing_node.line_number = min(existing_node.line_number, func_info.line_number)
        else:
            node = CallGraphNode(
                function_name=func_info.name,
                file_path=func_info.file_path,
                line_number=func_info.line_number
            )
            self.nodes[key] = node
            self.graph.add_node(key, data=node)
        
        assert key in self.nodes, "Node must be added"


def build_call_graph(functions: List[FunctionInfo]) -> CallGraph:
    """
    Build call graph from function information.
    
    Preconditions: functions is list of valid FunctionInfo
    Postconditions: returns complete CallGraph with edges
    """
    assert isinstance(functions, list), "Functions must be list"
    
    graph = CallGraph()
    
    unique_keys = set()
    for func in functions:
        key = create_function_key(func.name, func.file_path)
        unique_keys.add(key)
        graph.add_function(func)
    
    add_call_edges(graph, functions)
    
    assert len(graph.nodes) == len(unique_keys), f"All unique functions added: {len(graph.nodes)} nodes, {len(unique_keys)} unique functions"
    assert len(graph.nodes) > 0 or len(functions) == 0, "Graph must have nodes if functions provided"
    return graph


def add_call_edges(graph: CallGraph, functions: List[FunctionInfo]) -> None:
    """
    Add edges representing function calls.
    
    Preconditions: graph initialized, functions have call info
    Postconditions: graph contains all call edges
    """
    for func in functions:
        caller_key = create_function_key(func.name, func.file_path)
        if caller_key not in graph.nodes:
            continue
        
        caller_node = graph.nodes[caller_key]
        
        for callee_name in func.calls:
            callee_found = False
            for key in graph.nodes:
                node = graph.nodes[key]
                if node.function_name == callee_name:
                    callee_key = key
                    add_edge(graph, caller_key, callee_key)
                    caller_node.callees.add(callee_key)
                    graph.nodes[callee_key].callers.add(caller_key)
                    callee_found = True
                    break


def add_edge(graph: CallGraph, caller: str, callee: str) -> None:
    """
    Add directed edge from caller to callee.
    
    Preconditions: both functions exist in graph
    Postconditions: edge added to graph
    """
    assert caller in graph.nodes, "Caller must exist"
    assert callee in graph.nodes, "Callee must exist"
    
    graph.graph.add_edge(caller, callee)


def find_entry_points(graph: CallGraph) -> List[str]:
    """
    Find functions with no callers (entry points).
    
    Preconditions: graph is populated
    Postconditions: returns list of entry point function keys
    """
    assert graph is not None, "Graph required"
    
    entry_points = []
    
    for key, node in graph.nodes.items():
        if len(node.callers) == 0:
            entry_points.append(key)
    
    assert isinstance(entry_points, list), "Result must be list"
    return entry_points


def get_call_path(
    graph: CallGraph,
    start: str,
    end: str
) -> Optional[List[str]]:
    """
    Find call path between two functions.
    
    Preconditions: start and end exist in graph
    Postconditions: returns path list or None if no path exists
    """
    assert start in graph.nodes, "Start function must exist"
    assert end in graph.nodes, "End function must exist"
    
    try:
        path = nx.shortest_path(graph.graph, start, end)
        return path
    except nx.NetworkXNoPath:
        return None


def get_abstraction_depth(graph: CallGraph, function_key: str) -> int:
    """
    Calculate abstraction depth (distance from entry points).
    
    Preconditions: function exists in graph
    Postconditions: returns non-negative depth value
    """
    assert function_key in graph.nodes, "Function must exist"
    
    entry_points = find_entry_points(graph)
    if not entry_points:
        return 0
    
    if function_key in entry_points:
        return 0
    
    min_depth = float('inf')
    
    for entry in entry_points:
        path = get_call_path(graph, entry, function_key)
        if path:
            min_depth = min(min_depth, len(path) - 1)
    
    result = 0 if min_depth == float('inf') else int(min_depth)
    assert result >= 0, "Depth must be non-negative"
    
    return result


def get_descendants(graph: CallGraph, function_key: str) -> Set[str]:
    """
    Get all functions called directly or indirectly.
    
    Preconditions: function exists in graph
    Postconditions: returns set of descendant function keys
    """
    assert function_key in graph.nodes, "Function must exist"
    
    descendants = set()
    visit_descendants(graph, function_key, descendants)
    
    assert isinstance(descendants, set), "Result must be set"
    return descendants


def visit_descendants(
    graph: CallGraph,
    current: str,
    visited: Set[str]
) -> None:
    """
    Recursively visit all descendants.
    
    Preconditions: current exists, visited set provided
    Postconditions: visited contains all descendant keys
    """
    node = graph.nodes[current]
    
    for callee_key in node.callees:
        if callee_key not in visited:
            visited.add(callee_key)
            visit_descendants(graph, callee_key, visited)
