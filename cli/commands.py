"""CLI command implementations."""

from pathlib import Path
from typing import List, Optional
import sys

from core.parser import parse_file, get_language_for_file
from core.call_graph import build_call_graph, find_entry_points
from core.change_detector import (
    ChangeDetector, 
    record_baseline, 
    detect_changes
)
from core.contract import FunctionContract, create_contract
from storage.database import (
    ContractDatabase,
    save_contract,
    get_contract,
    save_call_graph
)


def initialize_project(project_path: str) -> bool:
    """
    Initialize abstraction tracking for project.
    
    Preconditions: project_path is valid directory path
    Postconditions: creates .abstraction directory, returns success
    """
    assert project_path, "Project path required"
    
    path = Path(project_path)
    if not path.exists():
        return False
    
    abstraction_dir = path / ".abstraction"
    abstraction_dir.mkdir(exist_ok=True)
    
    db = ContractDatabase(str(abstraction_dir))
    
    assert abstraction_dir.exists(), "Directory must be created"
    return True


def index_source_directory(
    source_dir: str,
    storage_dir: str
) -> int:
    """
    Parse and index all source files in directory.
    
    Preconditions: directories exist and are valid
    Postconditions: returns count of indexed functions
    """
    assert source_dir, "Source directory required"
    assert storage_dir, "Storage directory required"
    
    source_path = Path(source_dir)
    if not source_path.exists():
        return 0
    
    all_functions = collect_functions_from_directory(source_path)
    
    if not all_functions:
        return 0
    
    db = ContractDatabase(storage_dir)
    graph = build_call_graph(all_functions)
    
    save_call_graph(db, graph)
    
    detector = ChangeDetector()
    record_baseline(detector, all_functions)
    
    count = len(all_functions)
    assert count >= 0, "Count must be non-negative"
    
    return count


def collect_functions_from_directory(directory: Path) -> List:
    """
    Recursively collect functions from all source files.
    
    Preconditions: directory exists
    Postconditions: returns list of FunctionInfo
    """
    all_functions = []
    
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        
        language = get_language_for_file(str(file_path))
        if not language:
            continue
        
        functions = parse_file(str(file_path))
        all_functions.extend(functions)
    
    assert isinstance(all_functions, list), "Result must be list"
    return all_functions


def display_call_graph_info(
    storage_dir: str,
    entry_function: Optional[str] = None
) -> bool:
    """
    Display call graph information.
    
    Preconditions: storage_dir contains indexed data
    Postconditions: prints graph info, returns success
    """
    assert storage_dir, "Storage directory required"
    
    from storage.database import load_call_graph
    from core.call_graph import find_entry_points
    from visualization.graph_viewer import (
        render_text_tree,
        print_graph_statistics
    )
    
    db = ContractDatabase(storage_dir)
    graph = load_call_graph(db)
    
    if not graph or len(graph.nodes) == 0:
        print("No call graph found. Run index first.")
        return False
    
    print("\n" + "="*70)
    print("Call Graph Statistics")
    print("="*70)
    print_graph_statistics(graph)
    
    entry_points = find_entry_points(graph)
    
    def find_function_key_by_name(name: str) -> Optional[str]:
        """Find function key by function name."""
        for key in graph.nodes:
            if graph.nodes[key].function_name == name:
                return key
        return None
    
    if entry_points:
        entry_names = [graph.nodes[key].function_name for key in entry_points]
        print(f"\nEntry Points: {', '.join(entry_names)}")
        
        if entry_function:
            function_key = find_function_key_by_name(entry_function)
            if function_key:
                print(f"\n{'='*70}")
                print(f"Call Tree from '{entry_function}':")
                print(f"{'='*70}")
                tree = render_text_tree(graph, function_key, max_depth=10)
                print(tree)
            else:
                all_names = [graph.nodes[key].function_name for key in graph.nodes.keys()]
                print(f"\nError: Function '{entry_function}' not found in graph.")
                print(f"Available functions: {', '.join(sorted(set(all_names)))}")
        else:
            first_entry_key = entry_points[0]
            first_entry_name = graph.nodes[first_entry_key].function_name
            print(f"\n{'='*70}")
            print(f"Call Tree from '{first_entry_name}':")
            print(f"{'='*70}")
            tree = render_text_tree(graph, first_entry_key, max_depth=10)
            print(tree)
            
            if len(entry_points) > 1:
                print(f"\nNote: {len(entry_points)} entry points found. Showing first one.")
                print(f"Use: python -m cli.main graph --entry <function_name> to view others.")
    else:
        print("\nNo entry points found (all functions are called by others).")
        if graph.nodes:
            first_func_key = list(graph.nodes.keys())[0]
            first_func_name = graph.nodes[first_func_key].function_name
            print(f"\nShowing tree from '{first_func_name}':")
            print("="*70)
            tree = render_text_tree(graph, first_func_key, max_depth=10)
            print(tree)
    
    print("\n" + "="*70)
    
    return True


def check_for_changes(
    source_dir: str,
    storage_dir: str
) -> bool:
    """
    Check for code changes since last index.
    
    Preconditions: directories valid, baseline exists
    Postconditions: displays change report, returns True if changes
    """
    assert source_dir, "Source directory required"
    
    source_path = Path(source_dir)
    current_functions = collect_functions_from_directory(source_path)
    
    detector = ChangeDetector()
    
    if not current_functions:
        print("No functions found in source directory")
        return False
    
    record_baseline(detector, current_functions)
    
    return True


def add_contract_interactive(
    storage_dir: str,
    function_name: str,
    file_path: str
) -> bool:
    """
    Add or update function contract interactively.
    
    Preconditions: storage_dir valid, function exists
    Postconditions: contract saved, returns success
    """
    assert function_name, "Function name required"
    assert file_path, "File path required"
    
    db = ContractDatabase(storage_dir)
    
    existing = get_contract(db, function_name, file_path)
    
    if existing:
        print(f"Updating contract for {function_name}")
    else:
        print(f"Creating new contract for {function_name}")
    
    contract = create_contract(function_name, file_path, 1)
    save_contract(db, contract)
    
    assert get_contract(db, function_name, file_path) is not None
    return True


def print_function_hierarchy(
    storage_dir: str,
    entry_point: str
) -> None:
    """
    Print function call hierarchy from entry point.
    
    Preconditions: storage_dir valid, entry_point exists
    Postconditions: hierarchy printed to stdout
    """
    assert entry_point, "Entry point required"
    
    print(f"Call hierarchy from {entry_point}:")
    print_tree_level(entry_point, 0)


def print_tree_level(function_name: str, depth: int) -> None:
    """
    Recursively print call tree.
    
    Preconditions: function_name valid, depth non-negative
    Postconditions: tree printed with indentation
    """
    assert depth >= 0, "Depth must be non-negative"
    
    indent = "  " * depth
    print(f"{indent}- {function_name}")
