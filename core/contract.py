"""Function contract representation and management."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class AbstractionLevel(Enum):
    """Abstraction level indicators."""
    ENTRY_POINT = "entry_point"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SYSTEM = "system"


@dataclass
class FunctionContract:
    """
    Represents a function's behavioral contract.
    
    Preconditions: name, file_path, line_number must be non-empty/positive
    Postconditions: provides complete contract specification for a function
    """
    name: str
    file_path: str
    line_number: int
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    input_prediction: str = ""
    output_prediction: str = ""
    expected_behavior: str = ""
    abstraction_level: AbstractionLevel = AbstractionLevel.MEDIUM
    code_hash: str = ""
    last_verified: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate contract invariants."""
        assert self.name, "Function name cannot be empty"
        assert self.file_path, "File path cannot be empty"
        assert self.line_number > 0, "Line number must be positive"


def create_contract(
    name: str,
    file_path: str,
    line_number: int,
    preconditions: Optional[List[str]] = None,
    postconditions: Optional[List[str]] = None
) -> FunctionContract:
    """
    Create a function contract with validation.
    
    Preconditions:
    - name is non-empty string
    - file_path is non-empty string
    - line_number is positive integer
    
    Postconditions:
    - returns valid FunctionContract instance
    - all fields are properly initialized
    """
    assert name and isinstance(name, str), "Invalid name"
    assert line_number > 0, "Line number must be positive"
    
    contract = FunctionContract(
        name=name,
        file_path=file_path,
        line_number=line_number,
        preconditions=preconditions or [],
        postconditions=postconditions or []
    )
    
    assert contract.name == name, "Contract name mismatch"
    return contract


def validate_contract_completeness(contract: FunctionContract) -> bool:
    """
    Check if contract has minimum required information.
    
    Preconditions: contract is valid FunctionContract instance
    Postconditions: returns True if contract is complete, False otherwise
    """
    assert isinstance(contract, FunctionContract), "Invalid contract type"
    
    has_conditions = (
        len(contract.preconditions) > 0 or 
        len(contract.postconditions) > 0
    )
    has_predictions = bool(
        contract.input_prediction or 
        contract.output_prediction
    )
    
    is_complete = bool(has_conditions or has_predictions)
    assert isinstance(is_complete, bool), "Result must be boolean"
    
    return is_complete
