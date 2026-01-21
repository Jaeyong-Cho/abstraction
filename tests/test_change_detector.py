"""Tests for change detector module."""

import pytest
from core.change_detector import (
    ChangeDetector,
    record_baseline,
    detect_changes,
    create_function_key,
    extract_name_from_key
)
from core.parser import FunctionInfo, compute_code_hash


def test_change_detector_initialization():
    """
    Test detector initialization.
    
    Preconditions: none
    Postconditions: empty detector created
    """
    detector = ChangeDetector()
    
    assert len(detector.baseline) == 0
    assert len(detector.function_locations) == 0


def test_record_baseline_single_function():
    """
    Test recording baseline with single function.
    
    Preconditions: valid function info provided
    Postconditions: baseline contains function hash
    """
    detector = ChangeDetector()
    func = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def test_func(): pass",
        calls=[],
        code_hash="abc123"
    )
    
    record_baseline(detector, [func])
    
    assert len(detector.baseline) == 1
    assert "test.py::test_func" in detector.baseline


def test_detect_no_changes():
    """
    Test detection when no changes exist.
    
    Preconditions: baseline recorded, same functions provided
    Postconditions: no changes reported
    """
    detector = ChangeDetector()
    func = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def test_func(): pass",
        calls=[],
        code_hash="abc123"
    )
    
    record_baseline(detector, [func])
    report = detect_changes(detector, [func])
    
    assert len(report.modified_functions) == 0
    assert len(report.new_functions) == 0
    assert len(report.deleted_functions) == 0


def test_detect_modified_function():
    """
    Test detection of modified function.
    
    Preconditions: function changed after baseline
    Postconditions: modification detected
    """
    detector = ChangeDetector()
    
    original = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def test_func(): pass",
        calls=[],
        code_hash=compute_code_hash("def test_func(): pass")
    )
    
    record_baseline(detector, [original])
    
    modified = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def test_func(): return 42",
        calls=[],
        code_hash=compute_code_hash("def test_func(): return 42")
    )
    
    report = detect_changes(detector, [modified])
    
    assert len(report.modified_functions) == 1
    assert "test_func" in report.modified_functions


def test_detect_new_function():
    """
    Test detection of new function.
    
    Preconditions: function added after baseline
    Postconditions: new function detected
    """
    detector = ChangeDetector()
    
    func1 = FunctionInfo(
        name="existing",
        file_path="test.py",
        line_number=1,
        end_line_number=3,
        body="def existing(): pass",
        calls=[],
        code_hash="abc1"
    )
    
    record_baseline(detector, [func1])
    
    func2 = FunctionInfo(
        name="new_func",
        file_path="test.py",
        line_number=5,
        end_line_number=7,
        body="def new_func(): pass",
        calls=[],
        code_hash="abc2"
    )
    
    report = detect_changes(detector, [func1, func2])
    
    assert len(report.new_functions) == 1
    assert "new_func" in report.new_functions


def test_create_function_key_format():
    """
    Test function key format.
    
    Preconditions: name and path provided
    Postconditions: key has correct format
    """
    key = create_function_key("my_func", "path/to/file.py")
    
    assert "::" in key
    assert "my_func" in key
    assert "path/to/file.py" in key


def test_extract_name_from_key_format():
    """
    Test extracting name from key.
    
    Preconditions: valid key provided
    Postconditions: function name extracted
    """
    key = "path/to/file.py::my_function"
    name = extract_name_from_key(key)
    
    assert name == "my_function"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
