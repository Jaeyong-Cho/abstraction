"""Tests for contract module."""

import pytest
from core.contract import (
    FunctionContract,
    AbstractionLevel,
    create_contract,
    validate_contract_completeness
)


def test_create_contract_basic():
    """
    Test basic contract creation.
    
    Preconditions: valid parameters provided
    Postconditions: contract created with correct attributes
    """
    contract = create_contract("test_func", "test.py", 10)
    
    assert contract.name == "test_func"
    assert contract.file_path == "test.py"
    assert contract.line_number == 10


def test_create_contract_with_conditions():
    """
    Test contract creation with conditions.
    
    Preconditions: preconditions and postconditions provided
    Postconditions: contract contains all conditions
    """
    preconditions = ["input > 0", "input is int"]
    postconditions = ["returns positive result"]
    
    contract = create_contract(
        "validate_input",
        "validator.py",
        5,
        preconditions,
        postconditions
    )
    
    assert len(contract.preconditions) == 2
    assert len(contract.postconditions) == 1
    assert "input > 0" in contract.preconditions


def test_contract_validation_empty():
    """
    Test validation of empty contract.
    
    Preconditions: contract has no conditions or predictions
    Postconditions: validation returns False
    """
    contract = create_contract("empty_func", "empty.py", 1)
    
    is_complete = validate_contract_completeness(contract)
    
    assert is_complete is False


def test_contract_validation_with_conditions():
    """
    Test validation of contract with conditions.
    
    Preconditions: contract has preconditions
    Postconditions: validation returns True
    """
    contract = create_contract(
        "has_conditions",
        "test.py",
        1,
        ["input exists"]
    )
    
    is_complete = validate_contract_completeness(contract)
    
    assert is_complete is True


def test_contract_validation_with_predictions():
    """
    Test validation of contract with predictions.
    
    Preconditions: contract has input/output predictions
    Postconditions: validation returns True
    """
    contract = create_contract("predict_func", "test.py", 1)
    contract.input_prediction = "integer value"
    
    is_complete = validate_contract_completeness(contract)
    
    assert is_complete is True


def test_contract_invariants():
    """
    Test contract invariants are enforced.
    
    Preconditions: attempt to create invalid contract
    Postconditions: assertions catch invalid state
    """
    with pytest.raises(AssertionError):
        FunctionContract(name="", file_path="test.py", line_number=1)
    
    with pytest.raises(AssertionError):
        FunctionContract(name="func", file_path="", line_number=1)
    
    with pytest.raises(AssertionError):
        FunctionContract(name="func", file_path="test.py", line_number=0)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
