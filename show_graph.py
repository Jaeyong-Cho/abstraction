#!/usr/bin/env python3
"""Show graph visualization example."""

from pathlib import Path
from storage.database import ContractDatabase, load_call_graph
from core.call_graph import find_entry_points
from visualization.graph_viewer import (
    render_text_tree,
    print_graph_statistics
)

def main():
    storage_dir = str(Path.cwd() / ".abstraction")
    db = ContractDatabase(storage_dir)
    graph = load_call_graph(db)
    
    if not graph or len(graph.nodes) == 0:
        print("No call graph found. Run: python -m cli.main index examples/")
        return
    
    print("\n" + "="*70)
    print("Call Graph Statistics")
    print("="*70)
    print_graph_statistics(graph)
    
    entry_points = find_entry_points(graph)
    
    if entry_points:
        print(f"\nEntry Points: {', '.join(entry_points)}")
        print(f"\n{'='*70}")
        print(f"Call Tree from '{entry_points[0]}':")
        print(f"{'='*70}")
        tree = render_text_tree(graph, entry_points[0], max_depth=10)
        print(tree)
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
