"""Web server for visual abstraction tracking interface."""

from flask import Flask, jsonify, request, send_from_directory, send_from_directory
from pathlib import Path
from typing import Dict, Any, Optional
import json
import os
import traceback
from urllib.parse import unquote, quote

from storage.database import ContractDatabase, load_call_graph, get_contract, save_contract
from core.call_graph import CallGraph, CallGraphNode
from core.contract import FunctionContract, AbstractionLevel, create_contract
from core.parser import parse_file, get_language_for_file
from cli.commands import index_source_directory, initialize_project


def create_app(storage_dir: str) -> Flask:
    """
    Create Flask application.
    
    Preconditions: storage_dir is valid directory path
    Postconditions: returns configured Flask app
    """
    assert storage_dir, "Storage directory required"
    
    app = Flask(__name__)
    app.config['STORAGE_DIR'] = storage_dir
    
    register_routes(app)
    
    assert app is not None, "App must be created"
    return app


def register_routes(app: Flask) -> None:
    """
    Register all API routes.
    
    Preconditions: app is Flask instance
    Postconditions: routes registered
    """
    assert app is not None, "App required"
    
    @app.route('/')
    def index() -> str:
        """Serve React app index page."""
        frontend_build = Path(__file__).parent.parent / 'frontend' / 'dist' / 'index.html'
        
        if frontend_build.exists():
            return frontend_build.read_text(encoding='utf-8')
        
        static_dir = Path(__file__).parent / 'static'
        index_file = static_dir / 'index.html'
        
        if index_file.exists():
            return index_file.read_text(encoding='utf-8')
        
        return "Frontend not found. Please build React app or create web/static/index.html", 404
    
    @app.route('/<path:path>')
    def serve_static(path: str) -> Any:
        """Serve static files from React build."""
        frontend_dist = Path(__file__).parent.parent / 'frontend' / 'dist'
        file_path = frontend_dist / path
        
        if file_path.exists() and file_path.is_file() and file_path.suffix in ['.js', '.css', '.json', '.svg', '.png', '.jpg', '.ico', '.woff', '.woff2', '.ttf', '.eot']:
            return send_from_directory(str(frontend_dist), path)
        
        if not path.startswith('api/'):
            return index()
        
        return jsonify({'error': 'Not found'}), 404
    
    @app.route('/api/graph')
    def get_graph() -> Dict[str, Any]:
        """
        Get call graph data.
        
        Preconditions: storage directory initialized
        Postconditions: returns graph data as JSON
        """
        storage_dir = app.config['STORAGE_DIR']
        db = ContractDatabase(storage_dir)
        graph = load_call_graph(db)
        
        if not graph:
            return jsonify({
                'nodes': [],
                'edges': [],
                'error': 'No graph found. Run index first.'
            })
        
        nodes_data = serialize_nodes_for_frontend(graph, db)
        edges_data = serialize_edges_for_frontend(graph)
        
        result = {
            'nodes': nodes_data,
            'edges': edges_data
        }
        
        assert isinstance(result, dict), "Result must be dict"
        return jsonify(result)
    
    @app.route('/api/contract/', defaults={'function_key': ''}, methods=['GET'])
    @app.route('/api/contract/<path:function_key>', methods=['GET'])
    def get_function_contract(function_key: str) -> Dict[str, Any]:
        """
        Get contract for specific function.
        
        Preconditions: function_key is valid identifier
        Postconditions: returns contract data or creates empty one
        """
        # Extract from request.path to handle URL encoding properly
        if not function_key:
            function_key = request.path.replace('/api/contract/', '')
        else:
            # Also try request.path as fallback for better URL encoding handling
            path_from_request = request.path.replace('/api/contract/', '')
            if path_from_request and path_from_request != function_key:
                # Use request.path if it seems more complete
                function_key = path_from_request
        
        function_key = unquote(function_key, encoding='utf-8')
        function_key = function_key.lstrip('/')
        function_key = '/' + function_key
        
        print(f"[DEBUG] contract GET - request.path: {repr(request.path)}")
        print(f"[DEBUG] contract GET - decoded: {repr(function_key)}")
        
        storage_dir = app.config['STORAGE_DIR']
        db = ContractDatabase(storage_dir)
        graph = load_call_graph(db)
        
        if graph and function_key not in graph.nodes:
            normalized_key = normalize_function_key(function_key, graph)
            if normalized_key:
                function_key = normalized_key
        
        contract = get_contract_by_key(db, function_key)
        
        if not contract:
            contract = create_contract_from_key(db, function_key)
            if not contract:
                available_keys = list(graph.nodes.keys())[:10] if graph else []
                matching_keys = [k for k in (graph.nodes.keys() if graph else []) if '::' in function_key and function_key.split('::')[-1] in k]
                return jsonify({
                    'error': f'Function not found: {function_key}',
                    'debug': {
                        'requested_key': function_key,
                        'available_keys_sample': available_keys,
                        'matching_keys': matching_keys[:5]
                    }
                }), 404
        
        contract_data = serialize_contract_for_frontend(contract)
        
        assert isinstance(contract_data, dict), "Result must be dict"
        return jsonify(contract_data)
    
    @app.route('/api/contract/<path:function_key>', methods=['POST'])
    def update_function_contract(function_key: str) -> Dict[str, Any]:
        """
        Update or create contract with predictions.
        
        Preconditions: function_key valid, request contains JSON data
        Postconditions: contract created/updated, returns success status
        """
        # Always use request.path for better URL encoding handling
        # Flask's path converter may not properly decode URL-encoded characters
        path_from_request = request.path.replace('/api/contract/', '')
        if path_from_request:
            function_key = path_from_request
        elif not function_key:
            return jsonify({'error': 'Function key required'}), 400
        
        # Decode URL encoding
        function_key = unquote(function_key, encoding='utf-8')
        function_key = function_key.lstrip('/')
        function_key = '/' + function_key
        
        print(f"[DEBUG] contract POST - request.path: {repr(request.path)}")
        print(f"[DEBUG] contract POST - decoded: {repr(function_key)}")
        
        storage_dir = app.config['STORAGE_DIR']
        db = ContractDatabase(storage_dir)
        graph = load_call_graph(db)
        
        if graph and function_key not in graph.nodes:
            normalized_key = normalize_function_key(function_key, graph)
            if normalized_key:
                function_key = normalized_key
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        contract = get_contract_by_key(db, function_key)
        
        if not contract:
            contract = create_contract_from_key(db, function_key)
            if not contract:
                return jsonify({'error': 'Function not found in graph'}), 404
        
        update_contract_from_data(contract, data)
        save_contract(db, contract)
        
        contract_data = serialize_contract_for_frontend(contract)
        return jsonify({
            'success': True, 
            'message': 'Contract saved',
            'contract': contract_data
        })
    
    @app.route('/api/functions')
    def list_functions() -> Dict[str, Any]:
        """
        List all functions organized by directory and file.
        
        Preconditions: storage directory initialized
        Postconditions: returns tree structure of functions
        """
        storage_dir = app.config['STORAGE_DIR']
        workspace_path = app.config.get('WORKSPACE_PATH', '')
        db = ContractDatabase(storage_dir)
        graph = load_call_graph(db)
        
        if not graph:
            return jsonify({'tree': {}})
        
        tree = build_directory_tree(graph, db, workspace_path)
        
        assert isinstance(tree, dict), "Result must be dict"
        return jsonify({'tree': tree})
    
    @app.route('/api/function-graph/', defaults={'function_key': ''})
    @app.route('/api/function-graph/<path:function_key>')
    def get_function_graph(function_key: str) -> Dict[str, Any]:
        """
        Get callee/caller graph for specific function.
        
        Preconditions: function_key is valid identifier
        Postconditions: returns focused graph with callees and callers
        """
        if not function_key:
            function_key = request.path.replace('/api/function-graph/', '')
        
        function_key = unquote(function_key, encoding='utf-8')
        function_key = function_key.lstrip('/')
        function_key = '/' + function_key
        
        print(f"[DEBUG] function-graph - received: {repr(function_key)}")
        print(f"[DEBUG] function-graph - request.path: {request.path}")
        
        storage_dir = app.config['STORAGE_DIR']
        db = ContractDatabase(storage_dir)
        graph = load_call_graph(db)
        
        if not graph:
            return jsonify({'error': 'Graph not found'}), 404
        
        print(f"[DEBUG] function-graph - key in graph: {function_key in graph.nodes}")
        if function_key in graph.nodes:
            print(f"[DEBUG] function-graph - DIRECT MATCH!")
        
        if function_key not in graph.nodes:
            normalized_key = normalize_function_key(function_key, graph)
            if normalized_key:
                function_key = normalized_key
            else:
                matching_keys = [k for k in graph.nodes.keys() if function_key.split('::')[-1] in k] if '::' in function_key else []
                return jsonify({
                    'error': f'Function not found: {function_key}',
                    'debug': {
                        'requested_key': function_key,
                        'available_keys_sample': list(graph.nodes.keys())[:5],
                        'matching_keys': matching_keys[:5]
                    }
                }), 404
        
        focused_graph = build_focused_graph(graph, function_key, db)
        
        assert isinstance(focused_graph, dict), "Result must be dict"
        return jsonify(focused_graph)
    
    @app.route('/api/function-code/', defaults={'function_key': ''})
    @app.route('/api/function-code/<path:function_key>')
    def get_function_code(function_key: str) -> Dict[str, Any]:
        """
        Get source code for specific function.
        
        Preconditions: function_key is valid identifier
        Postconditions: returns function source code with metadata
        """
        if not function_key:
            function_key = request.path.replace('/api/function-code/', '')
        
        function_key = unquote(function_key, encoding='utf-8')
        function_key = function_key.lstrip('/')
        function_key = '/' + function_key
        
        print(f"[DEBUG] function-code - received: {repr(function_key)}")
        
        storage_dir = app.config['STORAGE_DIR']
        db = ContractDatabase(storage_dir)
        graph = load_call_graph(db)
        
        if not graph:
            return jsonify({'error': 'Graph not found'}), 404
        
        if function_key not in graph.nodes:
            normalized_key = normalize_function_key(function_key, graph)
            if normalized_key:
                function_key = normalized_key
            else:
                matching_keys = [k for k in graph.nodes.keys() if function_key.split('::')[-1] in k] if '::' in function_key else []
                return jsonify({
                    'error': f'Function not found: {function_key}',
                    'debug': {
                        'requested_key': function_key,
                        'available_keys_sample': list(graph.nodes.keys())[:5],
                        'matching_keys': matching_keys[:5]
                    }
                }), 404
        
        node = graph.nodes[function_key]
        code_data = extract_function_code(node, graph)
        
        assert isinstance(code_data, dict), "Result must be dict"
        return jsonify(code_data)
    
    @app.route('/api/workspace', methods=['GET', 'POST'])
    def workspace() -> Dict[str, Any]:
        """
        Get or set workspace path.
        
        Preconditions: GET returns current workspace, POST requires JSON with 'path'
        Postconditions: GET returns workspace path, POST sets workspace and returns success
        """
        if request.method == 'GET':
            workspace = app.config.get('WORKSPACE_PATH', '')
            return jsonify({'workspace': workspace})
        
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'error': 'Path required'}), 400
        
        workspace_path = str(data['path']).strip()
        if not workspace_path:
            return jsonify({'error': 'Path cannot be empty'}), 400
        
        path_obj = Path(workspace_path)
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj
        
        if not path_obj.exists():
            return jsonify({'error': f'Path does not exist: {path_obj}'}), 400
        
        if not path_obj.is_dir():
            return jsonify({'error': 'Path must be a directory'}), 400
        
        workspace_path = str(path_obj.resolve())
        
        app.config['WORKSPACE_PATH'] = workspace_path
        
        return jsonify({'success': True, 'workspace': workspace_path})
    
    @app.route('/api/index', methods=['POST'])
    def index_workspace() -> Dict[str, Any]:
        """
        Index source directory in workspace.
        
        Preconditions: workspace path is set
        Postconditions: source directory indexed, returns function count
        """
        workspace_path = app.config.get('WORKSPACE_PATH')
        storage_dir = app.config.get('STORAGE_DIR')
        
        if not workspace_path:
            error_msg = 'Workspace not set. Please set workspace first.'
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'debug': {
                    'workspace_path': workspace_path,
                    'storage_dir': storage_dir
                }
            }), 400
        
        workspace_path_obj = Path(workspace_path)
        if not workspace_path_obj.exists():
            error_msg = f'Workspace path does not exist: {workspace_path}'
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'debug': {
                    'workspace_path': workspace_path,
                    'resolved_path': str(workspace_path_obj.resolve()) if workspace_path_obj.is_absolute() else 'relative'
                }
            }), 400
        
        if not workspace_path_obj.is_dir():
            error_msg = f'Workspace path is not a directory: {workspace_path}'
            print(f"[ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        storage_path_obj = Path(storage_dir)
        if not storage_path_obj.exists():
            try:
                project_root = storage_path_obj.parent
                if not project_root.exists():
                    return jsonify({
                        'success': False,
                        'error': f'Project root directory does not exist: {project_root}'
                    }), 400
                
                if not initialize_project(str(project_root)):
                    return jsonify({
                        'success': False,
                        'error': f'Failed to initialize storage directory: {storage_dir}'
                    }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to initialize storage: {str(e)}'
                }), 500
        
        try:
            count = index_source_directory(str(workspace_path_obj.resolve()), str(storage_path_obj.resolve()))
            return jsonify({
                'success': True,
                'count': count,
                'message': f'Indexed {count} functions'
            })
        except AssertionError as e:
            return jsonify({
                'success': False,
                'error': f'Validation error: {str(e)}'
            }), 400
        except Exception as e:
            error_trace = traceback.format_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': error_trace
            }), 500


def serialize_nodes_for_frontend(graph: CallGraph, db: ContractDatabase) -> list:
    """
    Convert graph nodes to frontend format.
    
    Preconditions: graph and db are valid
    Postconditions: returns list of node dictionaries
    """
    assert graph is not None, "Graph required"
    assert db is not None, "Database required"
    
    nodes = []
    file_colors = get_file_color_map(graph)
    
    for key, node in graph.nodes.items():
        contract = get_contract_by_key(db, key)
        
        node_data = {
            'id': key,
            'label': node.function_name,
            'file': node.file_path,
            'line': node.line_number,
            'hasContract': contract is not None,
            'hasPredictions': has_predictions(contract),
            'abstractionLevel': get_abstraction_level(contract),
            'fileColor': file_colors.get(node.file_path, '#ecf0f1')
        }
        
        nodes.append(node_data)
    
    assert isinstance(nodes, list), "Result must be list"
    return nodes


def get_file_color_map(graph: CallGraph) -> Dict[str, str]:
    """
    Generate color map for files.
    
    Preconditions: graph is valid
    Postconditions: returns dict mapping file paths to colors
    """
    assert graph is not None, "Graph required"
    
    files = set()
    for node in graph.nodes.values():
        files.add(node.file_path)
    
    colors = [
        '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
        '#1abc9c', '#e67e22', '#34495e', '#16a085', '#27ae60',
        '#2980b9', '#8e44ad', '#c0392b', '#d35400', '#7f8c8d'
    ]
    
    file_colors = {}
    for idx, file_path in enumerate(sorted(files)):
        file_colors[file_path] = colors[idx % len(colors)]
    
    assert isinstance(file_colors, dict), "Result must be dict"
    return file_colors


def serialize_edges_for_frontend(graph: CallGraph) -> list:
    """
    Convert graph edges to frontend format with direction labels.
    
    Preconditions: graph is valid
    Postconditions: returns list of edge dictionaries with labels
    """
    assert graph is not None, "Graph required"
    
    edges = []
    
    for key, node in graph.nodes.items():
        caller_name = node.function_name
        for callee_key in node.callees:
            callee_node = graph.nodes.get(callee_key)
            callee_name = callee_node.function_name if callee_node else ''
            
            edge_data = {
                'from': key,
                'to': callee_key,
                'label': '→',
                'arrows': 'to',
                'smooth': {'type': 'curvedCW', 'roundness': 0.3}
            }
            edges.append(edge_data)
    
    assert isinstance(edges, list), "Result must be list"
    return edges


def serialize_contract_for_frontend(contract: FunctionContract) -> Dict[str, Any]:
    """
    Convert contract to frontend format.
    
    Preconditions: contract is valid
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
        'expected_behavior': contract.expected_behavior or (
            (contract.input_prediction or '') + '\n\n' + (contract.output_prediction or '')
        ).strip(),
        'abstraction_level': contract.abstraction_level.value,
        'metadata': contract.metadata
    }
    
    assert isinstance(data, dict), "Result must be dict"
    return data


def get_contract_by_key(db: ContractDatabase, function_key: str) -> Optional[FunctionContract]:
    """
    Get contract by function key.
    
    Preconditions: db initialized, key is valid
    Postconditions: returns contract or None
    """
    assert function_key, "Function key required"
    
    if "::" not in function_key:
        return None
    
    file_path, function_name = function_key.split("::", 1)
    contract = get_contract(db, function_name, file_path)
    
    return contract


def create_contract_from_key(db: ContractDatabase, function_key: str) -> Optional[FunctionContract]:
    """
    Create contract from function key using graph data.
    
    Preconditions: db initialized, key exists in graph
    Postconditions: returns new contract or None
    """
    assert function_key, "Function key required"
    
    graph = load_call_graph(db)
    if not graph:
        return None
    
    if function_key not in graph.nodes:
        function_key_normalized = normalize_function_key(function_key, graph)
        if function_key_normalized and function_key_normalized in graph.nodes:
            function_key = function_key_normalized
        else:
            return None
    
    node = graph.nodes[function_key]
    contract = create_contract(
        name=node.function_name,
        file_path=node.file_path,
        line_number=node.line_number
    )
    
    assert contract.name == node.function_name, "Contract name must match"
    return contract


def normalize_function_key(function_key: str, graph: CallGraph) -> Optional[str]:
    """
    Try to normalize function key to match graph keys.
    
    Preconditions: function_key and graph are valid
    Postconditions: returns normalized key or None if not found
    """
    if "::" not in function_key:
        return None
    
    file_path_str, function_name = function_key.split("::", 1)
    
    for key in graph.nodes:
        if key == function_key:
            return key
        
        if "::" not in key:
            continue
        
        key_file_path, key_function_name = key.split("::", 1)
        
        if key_function_name != function_name:
            continue
        
        file_path_obj = Path(file_path_str)
        key_path_obj = Path(key_file_path)
        
        try:
            if file_path_obj.is_absolute() and key_path_obj.is_absolute():
                if file_path_obj.resolve() == key_path_obj.resolve():
                    return key
            elif str(file_path_obj) == str(key_path_obj):
                return key
            elif file_path_obj.is_absolute():
                try:
                    if file_path_obj.resolve() == key_path_obj.resolve():
                        return key
                except Exception:
                    pass
            elif key_path_obj.is_absolute():
                try:
                    if key_path_obj.resolve() == file_path_obj.resolve():
                        return key
                except Exception:
                    pass
        except Exception:
            continue
    
    return None


def build_directory_tree(graph: CallGraph, db: ContractDatabase, workspace_path: str = '') -> Dict[str, Any]:
    """
    Build nested directory-file-function tree structure.
    
    Preconditions: graph and db are valid
    Postconditions: returns nested dictionary structure with relative paths
    """
    assert graph is not None, "Graph required"
    assert db is not None, "Database required"
    
    tree: Dict[str, Any] = {}
    workspace_path_obj = Path(workspace_path).resolve() if workspace_path else None
    
    for key, node in graph.nodes.items():
        contract = get_contract_by_key(db, key)
        file_path = Path(node.file_path)
        
        if workspace_path_obj and file_path.is_absolute():
            try:
                relative_path = file_path.relative_to(workspace_path_obj)
                file_path_str = str(relative_path)
            except ValueError:
                file_path_str = node.file_path
        else:
            file_path_str = node.file_path
        
        parts = file_path_str.split('/')
        filename = parts[-1]
        directory_parts = parts[:-1] if len(parts) > 1 else []
        
        current = tree
        for dir_part in directory_parts:
            if dir_part not in current:
                current[dir_part] = {}
            current = current[dir_part]
        
        if filename not in current:
            current[filename] = []
        
        current[filename].append({
            'key': key,
            'name': node.function_name,
            'line': node.line_number,
            'has_predictions': has_predictions(contract)
        })
    
    assert isinstance(tree, dict), "Result must be dict"
    return tree


def build_focused_graph(
    graph: CallGraph,
    function_key: str,
    db: ContractDatabase
) -> Dict[str, Any]:
    """
    Build graph focused on specific function showing callees and callers.
    
    Preconditions: function_key exists in graph
    Postconditions: returns graph with center function, callers, and callees
    """
    assert function_key in graph.nodes, "Function must exist in graph"
    
    center_node = graph.nodes[function_key]
    included_keys = {function_key}
    
    for callee_key in center_node.callees:
        included_keys.add(callee_key)
    
    for caller_key in center_node.callers:
        included_keys.add(caller_key)
    
    nodes_data = []
    edges_data = []
    file_colors = get_file_color_map(graph)
    
    center_node = graph.nodes[function_key]
    
    for key in included_keys:
        node = graph.nodes[key]
        contract = get_contract_by_key(db, key)
        
        is_center = (key == function_key)
        
        level = 0
        if is_center:
            level = 1
        elif key in center_node.callers:
            level = 0
        elif key in center_node.callees:
            level = 2
        
        node_data = {
            'id': key,
            'label': node.function_name,
            'file': node.file_path,
            'line': node.line_number,
            'hasContract': contract is not None,
            'hasPredictions': has_predictions(contract),
            'abstractionLevel': get_abstraction_level(contract),
            'fileColor': file_colors.get(node.file_path, '#ecf0f1'),
            'isCenter': is_center,
            'level': level
        }
        
        nodes_data.append(node_data)
    
    for key in included_keys:
        node = graph.nodes[key]
        for callee_key in node.callees:
            if callee_key in included_keys:
                edges_data.append({
                    'from': key,
                    'to': callee_key,
                    'label': '→',
                    'arrows': 'to'
                })
    
    result = {
        'nodes': nodes_data,
        'edges': edges_data,
        'center': function_key
    }
    
    assert isinstance(result, dict), "Result must be dict"
    return result


def has_predictions(contract: Optional[FunctionContract]) -> bool:
    """
    Check if contract has predictions.
    
    Preconditions: contract may be None
    Postconditions: returns True if has predictions
    """
    if not contract:
        return False
    
    has_input = bool(contract.input_prediction and contract.input_prediction.strip())
    has_output = bool(contract.output_prediction and contract.output_prediction.strip())
    
    result = has_input or has_output
    assert isinstance(result, bool), "Result must be boolean"
    return result


def get_abstraction_level(contract: Optional[FunctionContract]) -> str:
    """
    Get abstraction level string.
    
    Preconditions: contract may be None
    Postconditions: returns level string
    """
    if not contract:
        return 'medium'
    
    return contract.abstraction_level.value


def extract_function_code(node: CallGraphNode, graph: CallGraph) -> Dict[str, Any]:
    """
    Extract function source code from file.
    
    Preconditions: node exists in graph
    Postconditions: returns code with caller/callee info
    """
    assert node is not None, "Node required"
    
    file_path = Path(node.file_path)
    if not file_path.exists():
        return {
            'code': '',
            'language': 'text',
            'start_line': node.line_number,
            'end_line': node.line_number,
            'callers': [],
            'callees': []
        }
    
    language = get_language_for_file(str(file_path))
    if not language:
        language = 'text'
    
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        functions = parse_file(str(file_path))
        target_func = None
        
        for func in functions:
            if func.name == node.function_name and func.line_number == node.line_number:
                target_func = func
                break
        
        if target_func:
            start_line = target_func.line_number - 1
            end_line = target_func.end_line_number
            code_lines = lines[start_line:end_line]
            code = '\n'.join(code_lines)
            
            caller_names = set()
            for caller_key in node.callers:
                if caller_key in graph.nodes:
                    caller_names.add(graph.nodes[caller_key].function_name)
            
            callee_names = set()
            for callee_key in node.callees:
                if callee_key in graph.nodes:
                    callee_names.add(graph.nodes[callee_key].function_name)
            
            return {
                'code': code,
                'language': language,
                'start_line': target_func.line_number,
                'end_line': target_func.end_line_number,
                'callers': list(caller_names),
                'callees': list(callee_names),
                'function_name': node.function_name
            }
        else:
            return {
                'code': content,
                'language': language,
                'start_line': node.line_number,
                'end_line': node.line_number + 10,
                'callers': [],
                'callees': []
            }
    except Exception as e:
        return {
            'code': f'Error reading file: {str(e)}',
            'language': 'text',
            'start_line': node.line_number,
            'end_line': node.line_number,
            'callers': [],
            'callees': []
        }


def update_contract_from_data(contract: FunctionContract, data: Dict[str, Any]) -> None:
    """
    Update contract fields from request data.
    
    Preconditions: contract valid, data contains update fields
    Postconditions: contract updated with new values
    """
    assert contract is not None, "Contract required"
    assert isinstance(data, dict), "Data must be dict"
    
    if 'expected_behavior' in data:
        contract.expected_behavior = str(data['expected_behavior'])
    
    if 'input_prediction' in data:
        contract.input_prediction = str(data['input_prediction'])
    
    if 'output_prediction' in data:
        contract.output_prediction = str(data['output_prediction'])
    
    if 'abstraction_level' in data:
        try:
            contract.abstraction_level = AbstractionLevel(data['abstraction_level'])
        except ValueError:
            pass
    
    if 'preconditions' in data:
        preconditions = data['preconditions']
        if isinstance(preconditions, list):
            contract.preconditions = [str(p) for p in preconditions]
    
    if 'postconditions' in data:
        postconditions = data['postconditions']
        if isinstance(postconditions, list):
            contract.postconditions = [str(p) for p in postconditions]
    
    if 'metadata' in data:
        if isinstance(data['metadata'], dict):
            contract.metadata.update(data['metadata'])
