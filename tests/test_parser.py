"""Tests for parser module."""

import pytest
from pathlib import Path
from core.parser import (
    compute_code_hash,
    get_language_for_file,
    FunctionInfo
)


def test_compute_code_hash_basic():
    """
    Test hash computation.
    
    Preconditions: code string provided
    Postconditions: returns 64-character hex hash
    """
    code = "def test(): pass"
    hash_value = compute_code_hash(code)
    
    assert len(hash_value) == 64
    assert all(c in '0123456789abcdef' for c in hash_value)


def test_compute_code_hash_deterministic():
    """
    Test hash is deterministic.
    
    Preconditions: same code hashed twice
    Postconditions: produces identical hashes
    """
    code = "int main() { return 0; }"
    
    hash1 = compute_code_hash(code)
    hash2 = compute_code_hash(code)
    
    assert hash1 == hash2


def test_compute_code_hash_different():
    """
    Test different code produces different hashes.
    
    Preconditions: two different code strings
    Postconditions: hashes are different
    """
    code1 = "def func1(): pass"
    code2 = "def func2(): pass"
    
    hash1 = compute_code_hash(code1)
    hash2 = compute_code_hash(code2)
    
    assert hash1 != hash2


def test_get_language_python():
    """
    Test language detection for Python.
    
    Preconditions: .py file path provided
    Postconditions: returns 'python'
    """
    language = get_language_for_file("test.py")
    
    assert language == "python"


def test_get_language_c():
    """
    Test language detection for C.
    
    Preconditions: .c or .h file path provided
    Postconditions: returns 'c'
    """
    assert get_language_for_file("test.c") == "c"
    assert get_language_for_file("test.h") == "c"


def test_get_language_cpp():
    """
    Test language detection for C++.
    
    Preconditions: C++ file extensions provided
    Postconditions: returns 'cpp'
    """
    assert get_language_for_file("test.cpp") == "cpp"
    assert get_language_for_file("test.hpp") == "cpp"
    assert get_language_for_file("test.cc") == "cpp"


def test_get_language_typescript():
    """
    Test language detection for TypeScript.
    
    Preconditions: .ts or .tsx file path provided
    Postconditions: returns 'typescript' or 'tsx'
    """
    assert get_language_for_file("test.ts") == "typescript"
    assert get_language_for_file("test.tsx") == "tsx"


def test_get_language_javascript():
    """
    Test language detection for JavaScript.
    
    Preconditions: .js or .jsx file path provided
    Postconditions: returns 'javascript' or 'jsx'
    """
    assert get_language_for_file("test.js") == "javascript"
    assert get_language_for_file("test.jsx") == "jsx"


def test_get_language_unknown():
    """
    Test language detection for unknown extension.
    
    Preconditions: unsupported file extension
    Postconditions: returns None
    """
    language = get_language_for_file("test.txt")
    
    assert language is None


def test_function_info_creation():
    """
    Test FunctionInfo creation.
    
    Preconditions: valid parameters provided
    Postconditions: FunctionInfo created correctly
    """
    func_info = FunctionInfo(
        name="test_func",
        file_path="test.py",
        line_number=1,
        end_line_number=5,
        body="def test_func(): pass",
        calls=["helper"],
        code_hash="abc123"
    )
    
    assert func_info.name == "test_func"
    assert func_info.line_number == 1
    assert len(func_info.calls) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
