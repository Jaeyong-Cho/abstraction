"""Integration tests for the complete system."""

import pytest
from pathlib import Path
import tempfile
import shutil

from core.parser import parse_file, FunctionInfo
from core.call_graph import build_call_graph, find_entry_points
from core.change_detector import (
    ChangeDetector,
    record_baseline,
    detect_changes
)
from core.contract import create_contract
from storage.database import (
    ContractDatabase,
    save_contract,
    get_contract
)


def test_end_to_end_python_parsing():
    """
    Test complete flow: parse Python file to call graph.
    
    Preconditions: sample Python file exists
    Postconditions: functions extracted and graph built
    """
    sample_file = Path("examples/sample_python.py")
    
    if not sample_file.exists():
        pytest.skip("Sample file not found")
    
    functions = parse_file(str(sample_file))
    
    assert len(functions) > 0
    
    function_names = [f.name for f in functions]
    assert "main" in function_names
    
    graph = build_call_graph(functions)
    assert len(graph.nodes) == len(functions)
    
    entry_points = find_entry_points(graph)
    assert "main" in entry_points


def test_end_to_end_change_detection():
    """
    Test complete change detection workflow.
    
    Preconditions: baseline recorded, code changed
    Postconditions: changes correctly detected
    """
    func1_v1 = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def test_func(): pass",
        calls=[],
        code_hash="hash_v1"
    )
    
    func1_v2 = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def test_func(): return 42",
        calls=[],
        code_hash="hash_v2"
    )
    
    detector = ChangeDetector()
    record_baseline(detector, [func1_v1])
    
    report = detect_changes(detector, [func1_v2])
    
    assert len(report.modified_functions) == 1
    assert "test_func" in report.modified_functions


def test_end_to_end_contract_persistence():
    """
    Test contract save and load workflow.
    
    Preconditions: temporary storage created
    Postconditions: contract persisted and retrieved correctly
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ContractDatabase(tmpdir)
        
        contract = create_contract(
            "my_function",
            "my_file.py",
            10,
            ["input > 0"],
            ["returns positive"]
        )
        
        save_contract(db, contract)
        
        retrieved = get_contract(db, "my_function", "my_file.py")
        
        assert retrieved is not None
        assert retrieved.name == "my_function"
        assert len(retrieved.preconditions) == 1


def test_abstraction_hierarchy_navigation():
    """
    Test navigating abstraction hierarchy.
    
    Preconditions: call graph with multiple levels
    Postconditions: can navigate from high to low abstraction
    """
    main_func = FunctionInfo(
        name="main",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def main(): process_data()",
        calls=["process_data"],
        code_hash="hash1"
    )
    
    process_func = FunctionInfo(
        name="process_data",
        file_path="test.py",
        line_number=5,
        end_line_number=7,
        body="def process_data(): calculate()",
        calls=["calculate"],
        code_hash="hash2"
    )
    
    calc_func = FunctionInfo(
        name="calculate",
        file_path="test.py",
        line_number=9,
        end_line_number=11,
        body="def calculate(): pass",
        calls=[],
        code_hash="hash3"
    )
    
    graph = build_call_graph([main_func, process_func, calc_func])
    
    assert "main" in graph.nodes
    assert "calculate" in graph.nodes["process_data"].callees
    
    entry_points = find_entry_points(graph)
    assert len(entry_points) == 1
    assert entry_points[0] == "main"


def test_contract_invalidation_on_change():
    """
    Test that contracts are flagged when code changes.
    
    Preconditions: contract exists, code changes
    Postconditions: affected contract identified
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db = ContractDatabase(tmpdir)
        
        contract = create_contract(
            "my_func",
            "test.py",
            1,
            ["input is positive"],
            ["output is doubled"]
        )
        contract.code_hash = "original_hash"
        
        save_contract(db, contract)
        
        original_func = FunctionInfo(
            name="my_func",
            file_path="test.py",
            line_number=1,
            end_line_number=3,
            body="def my_func(): pass",
            calls=[],
            code_hash="original_hash"
        )
        
        detector = ChangeDetector()
        record_baseline(detector, [original_func])
        
        modified_func = FunctionInfo(
            name="my_func",
            file_path="test.py",
            line_number=1,
            end_line_number=3,
            body="def my_func(): return 42",
            calls=[],
            code_hash="new_hash"
        )
        
        report = detect_changes(detector, [modified_func])
        
        assert "my_func" in report.affected_contracts


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
