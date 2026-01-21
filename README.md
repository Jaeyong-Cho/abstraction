# Abstraction Level Tracker

A practical system for tracking, recording, and navigating software abstraction levels through function contracts and call hierarchies.

## Quick Start

### Automated Setup

```bash
# Run setup script (installs all dependencies)
./setup.sh

# Initialize project
python -m cli.main init .

# Index your codebase
python -m cli.main index examples/

# Run in production mode (builds frontend automatically)
./run.sh

# Or run in development mode (hot reload for frontend)
./run-dev.sh
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Initialize project
python -m cli.main init .

# Index your codebase
python -m cli.main index examples/

# View call graph (terminal)
python -m cli.main graph

# Start web interface (visual)
python -m cli.main serve

# Run demo
python demo.py

# Run tests
pytest
```

## Core Concept

Human cognition relies on abstraction to manage complexity. In software:
- We predict behavior at each abstraction level
- When predictions fail (bugs), we must lower abstraction
- We should only lower as far as needed to explain the discrepancy
- After understanding, we re-abstract with the corrected model

This system makes those predictions explicit and traceable.

## Key Features

- **Function Contracts**: Explicit preconditions and postconditions
- **Call Graph Analysis**: Navigate from high to low abstraction
- **Visual Web Interface**: Modern React-based interface with interactive graph visualization and prediction recording
- **Change Detection**: Identify when code changes invalidate contracts
- **Multi-Language**: Python (full support), C, C++ (with optional packages)
- **Simple Storage**: JSON-based, human-readable, version-controllable
- **Complete Tests**: 32 tests, 100% pass rate

## Frontend Development

The web interface is built with React + TypeScript + Vite. For development:

```bash
cd frontend
npm install
npm run dev  # Starts Vite dev server with hot reload
```

The dev server runs on `http://localhost:5173` and proxies API requests to the Flask backend at `http://127.0.0.1:5000`.

For production, build the frontend:

```bash
cd frontend
npm run build
```

The built files are served automatically by Flask when running `python -m cli.main serve`.

## Project Structure

```
abstraction/
├── core/                   # Core functionality
│   ├── contract.py        # Function contract model
│   ├── parser.py          # Multi-language code parser
│   ├── call_graph.py      # Call graph construction
│   └── change_detector.py # Change tracking
├── storage/               # Persistence layer
│   └── database.py        # JSON-based storage
├── cli/                   # Command-line interface
│   ├── main.py           # CLI entry point
│   └── commands.py       # Command implementations
├── visualization/         # Graph rendering
│   └── graph_viewer.py   # Visualization tools
├── tests/                 # Comprehensive test suite
├── examples/              # Sample code
├── README.md             # This file
├── USAGE.md              # Detailed usage guide
├── EXAMPLES.md           # Practical examples
└── PROJECT_SUMMARY.md    # Complete project documentation
```

## Philosophy

When debugging:
1. Start at the highest abstraction level (entry point)
2. Follow the execution path
3. Lower abstraction where prediction fails
4. Stop when the discrepancy is explainable
5. Re-abstract with the corrected understanding

## Documentation

- **USAGE.md**: Complete usage guide with all commands
- **EXAMPLES.md**: Detailed examples and use cases
- **PROJECT_SUMMARY.md**: Full technical documentation

## Quick Example

```python
def process_data(value):
    """
    Process input value.
    
    Preconditions: value is positive integer
    Postconditions: returns value doubled
    """
    assert value > 0, "Value must be positive"
    
    result = value * 2
    
    assert result > value, "Result must be greater"
    return result
```

Track this with:
```bash
python -m cli.main index mycode.py
python -m cli.main graph
```

## Design Principles

This project follows strict design principles:
- Functions max 60 lines
- Single responsibility per function
- Explicit preconditions and postconditions
- Minimum 2 assertions per function
- Every function has test examples
- Max 2-level indentation
- Early returns, no deep nesting

## Requirements

- Python 3.8+
- tree-sitter and tree-sitter-python (required)
- tree-sitter-c, tree-sitter-cpp (optional, for C/C++ support)
- pytest (for testing)
- networkx (for graph operations)

## Status

All features implemented and tested:
- ✓ Function contract model
- ✓ Multi-language parser
- ✓ Call graph construction
- ✓ Change detection
- ✓ Persistent storage
- ✓ CLI interface
- ✓ Visualization
- ✓ Complete test suite
- ✓ Documentation and examples
