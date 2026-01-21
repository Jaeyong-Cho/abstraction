"""Code change detection and tracking."""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from pathlib import Path

from .parser import FunctionInfo, parse_file, compute_code_hash
from .contract import FunctionContract


@dataclass
class ChangeReport:
    """
    Report of detected changes in codebase.
    
    Preconditions: all fields properly initialized
    Postconditions: complete change summary
    """
    modified_functions: List[str]
    deleted_functions: List[str]
    new_functions: List[str]
    affected_contracts: List[str]


class ChangeDetector:
    """
    Detect changes in source code and flag outdated abstractions.
    
    Preconditions: baseline established with record_baseline
    Postconditions: provides change detection capabilities
    """
    
    def __init__(self) -> None:
        """
        Initialize change detector.
        
        Preconditions: none
        Postconditions: empty baseline ready for recording
        """
        self.baseline: Dict[str, str] = {}
        self.function_locations: Dict[str, str] = {}
        
        assert len(self.baseline) == 0, "Baseline starts empty"


def record_baseline(detector: ChangeDetector, functions: List[FunctionInfo]) -> None:
    """
    Record current state as baseline.
    
    Preconditions: detector initialized, functions valid
    Postconditions: baseline populated with function hashes
    """
    assert detector is not None, "Detector required"
    assert isinstance(functions, list), "Functions must be list"
    
    detector.baseline.clear()
    detector.function_locations.clear()
    
    unique_keys = set()
    for func in functions:
        key = create_function_key(func.name, func.file_path)
        unique_keys.add(key)
        detector.baseline[key] = func.code_hash
        detector.function_locations[func.name] = func.file_path
    
    assert len(detector.baseline) == len(unique_keys), f"All unique functions recorded: {len(detector.baseline)} baseline entries, {len(unique_keys)} unique functions"
    assert len(detector.baseline) > 0 or len(functions) == 0, "Baseline must have entries if functions provided"


def create_function_key(name: str, file_path: str) -> str:
    """
    Create unique key for function.
    
    Preconditions: name and file_path non-empty
    Postconditions: returns unique identifier string
    """
    assert name, "Name required"
    assert file_path, "File path required"
    
    key = f"{file_path}::{name}"
    
    assert "::" in key, "Key must contain separator"
    return key


def detect_changes(
    detector: ChangeDetector,
    current_functions: List[FunctionInfo]
) -> ChangeReport:
    """
    Detect changes compared to baseline.
    
    Preconditions: baseline recorded, current_functions valid
    Postconditions: returns complete change report
    """
    assert detector is not None, "Detector required"
    assert len(detector.baseline) > 0, "Baseline must be established"
    
    modified = []
    new = []
    current_keys = set()
    
    for func in current_functions:
        key = create_function_key(func.name, func.file_path)
        current_keys.add(key)
        
        if key not in detector.baseline:
            new.append(func.name)
        elif detector.baseline[key] != func.code_hash:
            modified.append(func.name)
    
    deleted = find_deleted_functions(detector, current_keys)
    affected = modified + new
    
    report = ChangeReport(
        modified_functions=modified,
        deleted_functions=deleted,
        new_functions=new,
        affected_contracts=affected
    )
    
    assert isinstance(report, ChangeReport), "Must return report"
    return report


def find_deleted_functions(
    detector: ChangeDetector,
    current_keys: Set[str]
) -> List[str]:
    """
    Find functions that existed in baseline but not in current.
    
    Preconditions: detector has baseline, current_keys valid
    Postconditions: returns list of deleted function names
    """
    deleted = []
    
    for key in detector.baseline:
        if key not in current_keys:
            func_name = extract_name_from_key(key)
            deleted.append(func_name)
    
    assert isinstance(deleted, list), "Result must be list"
    return deleted


def extract_name_from_key(key: str) -> str:
    """
    Extract function name from function key.
    
    Preconditions: key has format 'path::name'
    Postconditions: returns function name portion
    """
    assert "::" in key, "Key must contain separator"
    
    parts = key.split("::")
    name = parts[-1]
    
    assert name, "Name must not be empty"
    return name


def check_file_changes(
    detector: ChangeDetector,
    file_path: str
) -> Optional[List[str]]:
    """
    Check for changes in specific file.
    
    Preconditions: file_path valid, detector has baseline
    Postconditions: returns list of changed functions or None
    """
    assert file_path, "File path required"
    
    path = Path(file_path)
    if not path.exists():
        return None
    
    current_functions = parse_file(file_path)
    changed = []
    
    for func in current_functions:
        key = create_function_key(func.name, file_path)
        if key in detector.baseline:
            if detector.baseline[key] != func.code_hash:
                changed.append(func.name)
    
    return changed


def update_baseline_for_function(
    detector: ChangeDetector,
    func_info: FunctionInfo
) -> None:
    """
    Update baseline for single function.
    
    Preconditions: detector initialized, func_info valid
    Postconditions: baseline updated with new hash
    """
    assert detector is not None, "Detector required"
    assert func_info is not None, "Function info required"
    
    key = create_function_key(func_info.name, func_info.file_path)
    old_hash = detector.baseline.get(key)
    
    detector.baseline[key] = func_info.code_hash
    detector.function_locations[func_info.name] = func_info.file_path
    
    assert detector.baseline[key] == func_info.code_hash, "Hash updated"


def is_contract_affected(
    change_report: ChangeReport,
    contract: FunctionContract
) -> bool:
    """
    Check if contract is affected by changes.
    
    Preconditions: change_report and contract valid
    Postconditions: returns True if contract needs update
    """
    assert change_report is not None, "Report required"
    assert contract is not None, "Contract required"
    
    all_changed = (
        change_report.modified_functions +
        change_report.new_functions +
        change_report.deleted_functions
    )
    
    is_affected = contract.name in all_changed
    assert isinstance(is_affected, bool), "Result must be boolean"
    
    return is_affected
