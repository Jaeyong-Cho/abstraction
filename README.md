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

From the research on abstraction:

> "추상화는 기본값이지만, 예측이 어긋나기 시작하면 실행·상태·시간 축을 따라 설명이 가능해질 때까지만 정확히 내려가야 한다."

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

## Web Interface (Visual)

시각적으로 호출 그래프를 탐색하고 각 함수의 추상화 예측을 기록할 수 있습니다:

```bash
# 웹 서버 시작 (기본 포트 5000)
python -m cli.main serve

# 다른 포트 사용
python -m cli.main serve 8080
```

브라우저에서 `http://localhost:5000`을 열면:
- **인터랙티브 그래프**: 함수 간 호출 관계를 시각적으로 탐색
- **예측 기록**: 각 함수를 클릭하여 입력/출력 예측을 기록
- **추상화 레벨 설정**: Entry Point, High, Medium, Low, System 중 선택
- **색상 표시**: 
  - 녹색: 예측이 기록된 함수
  - 주황색: 계약만 있는 함수
  - 회색: 계약이 없는 함수

## 시각화 예시 (Terminal)

시스템은 호출 그래프를 텍스트 트리로 시각화합니다:

```bash
# 기본 사용
python -m cli.main graph

# 특정 함수부터
python -m cli.main graph --entry main

# 데모 실행
python demo_visualization.py
```

### 출력 예시

```
======================================================================
Call Graph Statistics
======================================================================
Total functions: 6
Total calls: 5
Average calls per function: 0.83

Entry Points: main

======================================================================
Call Tree from 'main':
======================================================================
- main
  - process_data
    - calculate_intermediate
    - apply_transformation
  - format_result
  - display_output
```

### 추상화 레벨 해석

이 트리는 추상화 레벨을 시각적으로 보여줍니다:

- **Level 0** (Entry Point): `main` - 프로그램 진입점
- **Level 1** (High-Level): `process_data`, `format_result`, `display_output` - 비즈니스 로직
- **Level 2** (Mid-Level): `calculate_intermediate`, `apply_transformation` - 세부 연산

### 디버깅 활용

예측이 틀렸을 때:
1. **Level 0**에서 시작 → 예상과 다름
2. **Level 1**로 내려감 → `process_data` 확인
3. **Level 2**로 내려감 → `apply_transformation`에서 버그 발견
4. 수정 후 재추상화

더 자세한 시각화 가이드는 **VISUALIZATION.md**를 참조하세요.

## Testing

All tests pass:
```bash
pytest                  # Run all 32 tests
pytest -m unit         # Unit tests only
pytest -m integration  # Integration tests
pytest --cov           # With coverage
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

## License

This is a demonstration project for abstraction-level tracking in software development.
