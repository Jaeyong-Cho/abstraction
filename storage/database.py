"""Metadata storage and retrieval."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from core.contract import FunctionContract, AbstractionLevel
from core.call_graph import CallGraph, CallGraphNode


class ContractDatabase:
    """
    Persistent storage for function contracts and metadata.
    
    Preconditions: storage_path is valid directory
    Postconditions: provides CRUD operations for contracts
    """
    
    def __init__(self, storage_path: str) -> None:
        """
        Initialize database at storage path.
        
        Preconditions: storage_path is valid path string
        Postconditions: database ready, directory created if needed
        """
        assert storage_path, "Storage path required"
        
        self.storage_path = Path(storage_path)
        self.contracts_file = self.storage_path / "contracts.json"
        self.graph_file = self.storage_path / "call_graph.json"
        
        initialize_storage(self.storage_path)
        
        assert self.storage_path.exists(), "Storage must exist"


def initialize_storage(path: Path) -> None:
    """
    Create storage directory if not exists.
    
    Preconditions: path is valid Path object
    Postconditions: directory exists
    """
    assert path is not None, "Path required"
    
    path.mkdir(parents=True, exist_ok=True)
    
    assert path.exists(), "Directory must be created"


def save_contract(db: ContractDatabase, contract: FunctionContract) -> None:
    """
    Save or update contract in database.
    
    Preconditions: db initialized, contract valid
    Postconditions: contract persisted to storage
    """
    assert db is not None, "Database required"
    assert contract is not None, "Contract required"
    
    contracts = load_all_contracts(db)
    key = create_contract_key(contract)
    contracts[key] = contract_to_dict(contract)
    
    write_contracts_file(db, contracts)
    
    assert key in load_all_contracts(db), "Contract must be saved"


def create_contract_key(contract: FunctionContract) -> str:
    """
    Create unique key for contract.
    
    Preconditions: contract has name and file_path
    Postconditions: returns unique identifier
    """
    assert contract.name, "Name required"
    assert contract.file_path, "File path required"
    
    key = f"{contract.file_path}::{contract.name}"
    
    assert "::" in key, "Key must contain separator"
    return key


def contract_to_dict(contract: FunctionContract) -> Dict:
    """
    Convert contract to dictionary for serialization.
    
    Preconditions: contract is valid FunctionContract
    Postconditions: returns serializable dictionary
    """
    assert contract is not None, "Contract required"
    
    data = {
        'name': contract.name,
        'file_path': contract.file_path,
        'line_number': contract.line_number,
        'preconditions': contract.preconditions,
        'postconditions': contract.postconditions,
        'input_prediction': contract.input_prediction,
        'output_prediction': contract.output_prediction,
        'expected_behavior': contract.expected_behavior,
        'abstraction_level': contract.abstraction_level.value,
        'code_hash': contract.code_hash,
        'last_verified': contract.last_verified,
        'metadata': contract.metadata
    }
    
    assert isinstance(data, dict), "Result must be dict"
    return data


def dict_to_contract(data: Dict) -> FunctionContract:
    """
    Convert dictionary to FunctionContract.
    
    Preconditions: data contains required fields
    Postconditions: returns valid FunctionContract
    """
    assert 'name' in data, "Name required in data"
    assert 'file_path' in data, "File path required"
    
    contract = FunctionContract(
        name=data['name'],
        file_path=data['file_path'],
        line_number=data['line_number'],
        preconditions=data.get('preconditions', []),
        postconditions=data.get('postconditions', []),
        input_prediction=data.get('input_prediction', ''),
        output_prediction=data.get('output_prediction', ''),
        expected_behavior=data.get('expected_behavior', ''),
        abstraction_level=AbstractionLevel(
            data.get('abstraction_level', 'medium')
        ),
        code_hash=data.get('code_hash', ''),
        last_verified=data.get('last_verified'),
        metadata=data.get('metadata', {})
    )
    
    assert contract.name == data['name'], "Name must match"
    return contract


def load_all_contracts(db: ContractDatabase) -> Dict:
    """
    Load all contracts from storage.
    
    Preconditions: db initialized
    Postconditions: returns dictionary of all contracts
    """
    assert db is not None, "Database required"
    
    if not db.contracts_file.exists():
        return {}
    
    content = db.contracts_file.read_text(encoding='utf-8')
    contracts = json.loads(content) if content else {}
    
    assert isinstance(contracts, dict), "Contracts must be dict"
    return contracts


def write_contracts_file(db: ContractDatabase, contracts: Dict) -> None:
    """
    Write contracts to file.
    
    Preconditions: db initialized, contracts valid dict
    Postconditions: contracts persisted to file
    """
    assert db is not None, "Database required"
    assert isinstance(contracts, dict), "Contracts must be dict"
    
    content = json.dumps(contracts, indent=2)
    db.contracts_file.write_text(content, encoding='utf-8')
    
    assert db.contracts_file.exists(), "File must exist after write"


def get_contract(
    db: ContractDatabase,
    function_name: str,
    file_path: str
) -> Optional[FunctionContract]:
    """
    Retrieve contract for specific function.
    
    Preconditions: db initialized, names provided
    Postconditions: returns contract or None
    """
    assert function_name, "Function name required"
    assert file_path, "File path required"
    
    contracts = load_all_contracts(db)
    key = f"{file_path}::{function_name}"
    
    if key not in contracts:
        return None
    
    return dict_to_contract(contracts[key])


def delete_contract(
    db: ContractDatabase,
    function_name: str,
    file_path: str
) -> bool:
    """
    Delete contract from database.
    
    Preconditions: db initialized
    Postconditions: contract removed if existed, returns success
    """
    assert function_name, "Function name required"
    
    contracts = load_all_contracts(db)
    key = f"{file_path}::{function_name}"
    
    if key not in contracts:
        return False
    
    del contracts[key]
    write_contracts_file(db, contracts)
    
    assert key not in load_all_contracts(db), "Contract must be deleted"
    return True


def save_call_graph(db: ContractDatabase, graph: CallGraph) -> None:
    """
    Persist call graph to storage.
    
    Preconditions: db initialized, graph valid
    Postconditions: graph saved to file
    """
    assert db is not None, "Database required"
    assert graph is not None, "Graph required"
    
    graph_data = serialize_call_graph(graph)
    content = json.dumps(graph_data, indent=2)
    db.graph_file.write_text(content, encoding='utf-8')
    
    assert db.graph_file.exists(), "Graph file must exist"


def serialize_call_graph(graph: CallGraph) -> Dict:
    """
    Convert call graph to serializable format.
    
    Preconditions: graph is valid CallGraph
    Postconditions: returns dictionary representation
    """
    nodes = {}
    
    for name, node in graph.nodes.items():
        nodes[name] = {
            'function_name': node.function_name,
            'file_path': node.file_path,
            'line_number': node.line_number,
            'callers': list(node.callers),
            'callees': list(node.callees)
        }
    
    assert isinstance(nodes, dict), "Result must be dict"
    return {'nodes': nodes}


def load_call_graph(db: ContractDatabase) -> Optional[CallGraph]:
    """
    Load call graph from storage.
    
    Preconditions: db initialized
    Postconditions: returns CallGraph or None if not found
    """
    assert db is not None, "Database required"
    
    if not db.graph_file.exists():
        return None
    
    content = db.graph_file.read_text(encoding='utf-8')
    if not content:
        return None
    
    graph_data = json.loads(content)
    
    from core.call_graph import CallGraph, CallGraphNode
    from core.parser import FunctionInfo
    
    graph = CallGraph()
    
    if 'nodes' not in graph_data:
        return graph
    
    from core.call_graph import create_function_key
    
    for key, node_data in graph_data['nodes'].items():
        node = CallGraphNode(
            function_name=node_data['function_name'],
            file_path=node_data['file_path'],
            line_number=node_data['line_number']
        )
        node.callers = set(node_data.get('callers', []))
        node.callees = set(node_data.get('callees', []))
        
        graph_key = key
        if "::" not in key:
            graph_key = create_function_key(node_data['function_name'], node_data['file_path'])
        
        graph.nodes[graph_key] = node
        graph.graph.add_node(graph_key, data=node)
    
    for key, node in graph.nodes.items():
        for callee_key in node.callees:
            if callee_key in graph.nodes:
                graph.graph.add_edge(key, callee_key)
    
    return graph
