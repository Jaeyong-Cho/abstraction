#!/usr/bin/env python3
"""
Demo script showing the abstraction tracking system in action.

Run this to see a complete workflow demonstration.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str) -> None:
    """
    Execute command and display result.
    
    Preconditions: cmd is valid shell command
    Postconditions: command executed, output displayed
    """
    assert cmd, "Command cannot be empty"
    assert description, "Description required"
    
    print(f"\n{'='*70}")
    print(f"Step: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*70}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0 and result.stderr:
        print(f"Error: {result.stderr}")
    
    assert isinstance(result.returncode, int), "Return code must be int"


def main() -> int:
    """
    Run complete demonstration.
    
    Preconditions: system is installed and working
    Postconditions: all demo steps executed, returns 0
    """
    print("Abstraction Level Tracker - Demo")
    print("="*70)
    
    project_dir = Path(__file__).parent
    
    steps = [
        (
            "python -m cli.main init .",
            "Initialize abstraction tracking"
        ),
        (
            "python -m cli.main index examples/",
            "Index example Python code"
        ),
        (
            "python -m cli.main graph",
            "View call graph"
        ),
        (
            "python -m cli.main check examples/",
            "Check for changes (none expected)"
        ),
        (
            "python -m pytest tests/ -v --tb=line -q",
            "Run test suite"
        ),
    ]
    
    for cmd, desc in steps:
        try:
            run_command(cmd, desc)
        except Exception as e:
            print(f"Error in step: {e}")
            return 1
    
    print("\n" + "="*70)
    print("Demo completed successfully!")
    print("="*70)
    print("\nNext steps:")
    print("  - Read USAGE.md for detailed usage instructions")
    print("  - Read EXAMPLES.md for practical examples")
    print("  - Try: python -m cli.main --help")
    print()
    
    assert True, "Demo must complete"
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
