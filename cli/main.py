"""Main CLI entry point."""

import sys
from pathlib import Path
from typing import List, Optional

from cli.commands import (
    initialize_project,
    index_source_directory,
    display_call_graph_info,
    check_for_changes,
    add_contract_interactive
)
from web.server import create_app


def print_usage() -> None:
    """
    Print usage information.
    
    Preconditions: none
    Postconditions: usage printed to stdout
    """
    usage = """
Abstraction Level Tracker

Usage:
  python -m cli.main init [path]              Initialize project
  python -m cli.main index <source_dir>       Index source code
  python -m cli.main graph                    Show call graph
  python -m cli.main check <source_dir>       Check for changes
  python -m cli.main contract <func> <file>   Add contract
  python -m cli.main serve [port]            Start web server

Options:
  -h, --help    Show this help message
"""
    print(usage.strip())


def run_init_command(args: List[str]) -> int:
    """
    Execute init command.
    
    Preconditions: args contains command arguments
    Postconditions: returns exit code (0 for success)
    """
    assert isinstance(args, list), "Args must be list"
    
    project_path = args[0] if args else "."
    
    success = initialize_project(project_path)
    
    if success:
        print(f"Initialized abstraction tracking in {project_path}")
        return 0
    
    print("Failed to initialize project")
    return 1


def run_index_command(args: List[str]) -> int:
    """
    Execute index command.
    
    Preconditions: args contains source directory
    Postconditions: returns exit code
    """
    assert isinstance(args, list), "Args must be list"
    
    if not args:
        print("Error: source directory required")
        return 1
    
    source_dir = args[0]
    storage_dir = str(Path.cwd() / ".abstraction")
    
    count = index_source_directory(source_dir, storage_dir)
    
    print(f"Indexed {count} functions")
    
    return 0


def run_graph_command(args: List[str]) -> int:
    """
    Execute graph command.
    
    Preconditions: args may contain entry function
    Postconditions: returns exit code
    """
    storage_dir = str(Path.cwd() / ".abstraction")
    
    entry = None
    if args:
        if args[0] == '--entry' and len(args) > 1:
            entry = args[1]
        elif not args[0].startswith('--'):
            entry = args[0]
    
    success = display_call_graph_info(storage_dir, entry)
    
    return 0 if success else 1


def run_check_command(args: List[str]) -> int:
    """
    Execute check command.
    
    Preconditions: args contains source directory
    Postconditions: returns exit code
    """
    if not args:
        print("Error: source directory required")
        return 1
    
    source_dir = args[0]
    storage_dir = str(Path.cwd() / ".abstraction")
    
    check_for_changes(source_dir, storage_dir)
    
    return 0


def run_contract_command(args: List[str]) -> int:
    """
    Execute contract command.
    
    Preconditions: args contains function name and file path
    Postconditions: returns exit code
    """
    if len(args) < 2:
        print("Error: function name and file path required")
        return 1
    
    func_name = args[0]
    file_path = args[1]
    storage_dir = str(Path.cwd() / ".abstraction")
    
    success = add_contract_interactive(storage_dir, func_name, file_path)
    
    return 0 if success else 1


def run_serve_command(args: List[str]) -> int:
    """
    Start web server for visual interface.
    
    Preconditions: args may contain port number
    Postconditions: starts Flask server, returns exit code
    """
    storage_dir = str(Path.cwd() / ".abstraction")
    
    if not Path(storage_dir).exists():
        print("Error: .abstraction directory not found. Run 'init' first.")
        return 1
    
    port = 5000
    if args:
        try:
            port = int(args[0])
            assert port > 0 and port < 65536, "Port must be 1-65535"
        except (ValueError, AssertionError):
            print(f"Error: Invalid port number: {args[0]}")
            return 1
    
    app = create_app(storage_dir)
    
    print(f"Starting web server on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        app.run(host='127.0.0.1', port=port, debug=False)
    except KeyboardInterrupt:
        print("\nServer stopped")
        return 0
    
    return 0


def main() -> int:
    """
    Main CLI entry point.
    
    Preconditions: sys.argv contains command line arguments
    Postconditions: returns exit code for shell
    """
    assert len(sys.argv) >= 1, "At least program name required"
    
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    commands = {
        'init': run_init_command,
        'index': run_index_command,
        'graph': run_graph_command,
        'check': run_check_command,
        'contract': run_contract_command,
        'serve': run_serve_command
    }
    
    if command in ['-h', '--help']:
        print_usage()
        return 0
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print_usage()
        return 1
    
    exit_code = commands[command](args)
    
    assert isinstance(exit_code, int), "Exit code must be integer"
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
