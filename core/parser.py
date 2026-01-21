"""Code parsing for multiple languages."""

import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

TREE_SITTER_AVAILABLE = False
AVAILABLE_LANGUAGES = {}

try:
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
    
    try:
        import tree_sitter_python
        AVAILABLE_LANGUAGES['python'] = tree_sitter_python
    except ImportError:
        pass
    
    try:
        import tree_sitter_c
        AVAILABLE_LANGUAGES['c'] = tree_sitter_c
    except ImportError:
        pass
    
    try:
        import tree_sitter_cpp
        AVAILABLE_LANGUAGES['cpp'] = tree_sitter_cpp
    except ImportError:
        pass
    
    try:
        import tree_sitter_typescript
        AVAILABLE_LANGUAGES['typescript'] = tree_sitter_typescript
        AVAILABLE_LANGUAGES['tsx'] = tree_sitter_typescript
    except ImportError:
        pass
    
    try:
        import tree_sitter_javascript
        AVAILABLE_LANGUAGES['javascript'] = tree_sitter_javascript
        AVAILABLE_LANGUAGES['jsx'] = tree_sitter_javascript
    except ImportError:
        pass
    
    if not AVAILABLE_LANGUAGES:
        TREE_SITTER_AVAILABLE = False
        
except ImportError:
    TREE_SITTER_AVAILABLE = False


@dataclass
class FunctionInfo:
    """
    Extracted function information from source code.
    
    Preconditions: name, file_path, line_number must be valid
    Postconditions: represents a complete function definition
    """
    name: str
    file_path: str
    line_number: int
    end_line_number: int
    body: str
    calls: List[str]
    code_hash: str


def compute_code_hash(code: str) -> str:
    """
    Compute SHA-256 hash of code content.
    
    Preconditions: code is a string
    Postconditions: returns 64-character hex string
    """
    assert isinstance(code, str), "Code must be string"
    
    hash_obj = hashlib.sha256(code.encode('utf-8'))
    result = hash_obj.hexdigest()
    
    assert len(result) == 64, "SHA-256 hash must be 64 chars"
    return result


def get_language_for_file(file_path: str) -> Optional[str]:
    """
    Determine language from file extension.
    
    Preconditions: file_path is non-empty string
    Postconditions: returns language identifier or None
    """
    assert file_path, "File path cannot be empty"
    
    suffix = Path(file_path).suffix.lower()
    language_map = {
        '.py': 'python',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.js': 'javascript',
        '.jsx': 'jsx'
    }
    
    result = language_map.get(suffix)
    assert result is None or isinstance(result, str), "Invalid result"
    
    return result


class CodeParser:
    """Multi-language code parser using tree-sitter."""
    
    def __init__(self) -> None:
        """
        Initialize parser with language support.
        
        Preconditions: tree-sitter libraries available
        Postconditions: parser ready for all supported languages
        """
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter not available")
        
        self.parsers: Dict[str, Parser] = {}
        self._initialize_parsers()
        
        assert len(self.parsers) > 0, "No parsers initialized"
    
    def _initialize_parsers(self) -> None:
        """
        Initialize parsers for supported languages.
        
        Preconditions: AVAILABLE_LANGUAGES populated
        Postconditions: parsers dict contains initialized parsers
        """
        assert len(AVAILABLE_LANGUAGES) > 0, "No languages available"
        
        for lang_name, lang_module in AVAILABLE_LANGUAGES.items():
            try:
                if lang_name == 'typescript':
                    lang_capsule = lang_module.language_typescript()
                elif lang_name == 'tsx':
                    lang_capsule = lang_module.language_tsx()
                elif lang_name in ['javascript', 'jsx']:
                    lang_capsule = lang_module.language()
                else:
                    lang_capsule = lang_module.language()
                
                language = Language(lang_capsule)
                parser = Parser(language)
                self.parsers[lang_name] = parser
            except Exception:
                continue


def extract_function_name(node: 'Node', language: str) -> Optional[str]:
    """
    Extract function name from AST node.
    
    Preconditions: node is valid tree-sitter Node
    Postconditions: returns function name or None
    """
    if not TREE_SITTER_AVAILABLE:
        return None
    
    assert node is not None, "Node cannot be None"
    
    if language in ['typescript', 'tsx', 'javascript', 'jsx']:
        return extract_js_function_name(node)
    
    name_patterns = {
        'python': ['name'],
        'c': ['declarator', 'function_declarator'],
        'cpp': ['declarator', 'function_declarator']
    }
    
    patterns = name_patterns.get(language, [])
    
    for pattern in patterns:
        name_node = node.child_by_field_name(pattern)
        if name_node:
            if name_node.type == 'identifier':
                return name_node.text.decode('utf-8')
            child = name_node.child_by_field_name('declarator')
            if child and child.type == 'identifier':
                return child.text.decode('utf-8')
    
    return None


def extract_js_function_name(node: 'Node') -> Optional[str]:
    """
    Extract function name from TypeScript/JavaScript AST node.
    
    Preconditions: node is valid tree-sitter Node for TS/JS
    Postconditions: returns function name or None
    """
    assert node is not None, "Node cannot be None"
    
    node_type = node.type
    
    if node_type == 'function_declaration':
        name_node = node.child_by_field_name('name')
        if name_node and name_node.type == 'identifier':
            return name_node.text.decode('utf-8')
    
    elif node_type == 'method_definition':
        name_node = node.child_by_field_name('name')
        if name_node:
            if name_node.type == 'property_identifier':
                return name_node.text.decode('utf-8')
            elif name_node.type == 'identifier':
                return name_node.text.decode('utf-8')
    
    elif node_type in ['function', 'arrow_function']:
        parent = node.parent
        if parent:
            if parent.type == 'variable_declarator':
                name_node = parent.child_by_field_name('name')
                if name_node and name_node.type == 'identifier':
                    return name_node.text.decode('utf-8')
            elif parent.type == 'assignment_expression':
                left = parent.child_by_field_name('left')
                if left:
                    if left.type == 'identifier':
                        return left.text.decode('utf-8')
                    elif left.type == 'member_expression':
                        prop = left.child_by_field_name('property')
                        if prop and prop.type == 'property_identifier':
                            return prop.text.decode('utf-8')
            elif parent.type == 'property_definition':
                name_node = parent.child_by_field_name('name')
                if name_node:
                    if name_node.type == 'property_identifier':
                        return name_node.text.decode('utf-8')
                    elif name_node.type == 'identifier':
                        return name_node.text.decode('utf-8')
    
    return None


def parse_file(file_path: str) -> List[FunctionInfo]:
    """
    Parse source file and extract function information.
    
    Preconditions: file_path points to valid source file
    Postconditions: returns list of FunctionInfo for all functions
    """
    assert file_path, "File path cannot be empty"
    
    path = Path(file_path)
    if not path.exists():
        return []
    
    language = get_language_for_file(file_path)
    if not language:
        return []
    
    content = path.read_text(encoding='utf-8')
    functions = extract_functions(content, file_path, language)
    
    assert isinstance(functions, list), "Result must be list"
    return functions


def extract_functions(
    code: str,
    file_path: str,
    language: str
) -> List[FunctionInfo]:
    """
    Extract all functions from code using tree-sitter.
    
    Preconditions: code is valid source, language supported
    Postconditions: returns FunctionInfo for each function found
    """
    assert code is not None, "Code cannot be None"
    assert language in ['python', 'c', 'cpp', 'typescript', 'tsx', 'javascript', 'jsx'], "Unsupported language"
    
    if not TREE_SITTER_AVAILABLE:
        return []
    
    try:
        code_parser = CodeParser()
        parser = code_parser.parsers.get(language)
        if not parser:
            return []
        
        tree = parser.parse(bytes(code, 'utf-8'))
        functions = []
        
        function_types = {
            'python': 'function_definition',
            'c': 'function_definition',
            'cpp': 'function_definition',
            'typescript': ['function_declaration', 'method_definition', 'function', 'arrow_function'],
            'tsx': ['function_declaration', 'method_definition', 'function', 'arrow_function'],
            'javascript': ['function_declaration', 'method_definition', 'function', 'arrow_function'],
            'jsx': ['function_declaration', 'method_definition', 'function', 'arrow_function']
        }
        
        target_types = function_types.get(language, [])
        if isinstance(target_types, str):
            target_types = [target_types]
        
        cursor = tree.walk()
        
        for target_type in target_types:
            visit_nodes(cursor.node, target_type, functions, code, file_path, language)
        
        assert isinstance(functions, list), "Result must be list"
        return functions
    except Exception:
        return []


def visit_nodes(
    node: 'Node',
    target_type: str,
    functions: List[FunctionInfo],
    code: str,
    file_path: str,
    language: str
) -> None:
    """
    Recursively visit AST nodes to find functions.
    
    Preconditions: node is valid, functions list provided
    Postconditions: functions list populated with found functions
    """
    if node.type == target_type:
        func_info = create_function_info(node, code, file_path, language)
        if func_info:
            functions.append(func_info)
    
    for child in node.children:
        visit_nodes(child, target_type, functions, code, file_path, language)


def create_function_info(
    node: 'Node',
    code: str,
    file_path: str,
    language: str
) -> Optional[FunctionInfo]:
    """
    Create FunctionInfo from AST node.
    
    Preconditions: node represents function definition
    Postconditions: returns FunctionInfo or None if extraction fails
    """
    name = extract_function_name(node, language)
    if not name:
        return None
    
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    body = node.text.decode('utf-8')
    code_hash = compute_code_hash(body)
    calls = extract_function_calls(node)
    
    return FunctionInfo(
        name=name,
        file_path=file_path,
        line_number=start_line,
        end_line_number=end_line,
        body=body,
        calls=calls,
        code_hash=code_hash
    )


def extract_function_calls(node: 'Node') -> List[str]:
    """
    Extract function call names from AST node.
    
    Preconditions: node is valid tree-sitter Node
    Postconditions: returns list of called function names
    """
    calls = []
    collect_calls(node, calls)
    
    assert isinstance(calls, list), "Calls must be list"
    return calls


def collect_calls(node: 'Node', calls: List[str]) -> None:
    """
    Recursively collect function calls.
    
    Preconditions: node is valid tree-sitter Node
    Postconditions: calls list populated with function names
    """
    assert node is not None, "Node cannot be None"
    assert isinstance(calls, list), "Calls must be list"
    
    if node.type == 'call':
        func_node = node.child_by_field_name('function')
        if func_node and func_node.type == 'identifier':
            calls.append(func_node.text.decode('utf-8'))
    
    elif node.type == 'call_expression':
        func_node = node.child_by_field_name('function')
        if func_node:
            call_name = extract_call_name(func_node)
            if call_name:
                calls.append(call_name)
    
    elif node.type == 'new_expression':
        constructor_node = node.child_by_field_name('constructor')
        if constructor_node:
            call_name = extract_call_name(constructor_node)
            if call_name:
                calls.append(call_name)
    
    for child in node.children:
        collect_calls(child, calls)


def extract_call_name(node: 'Node') -> Optional[str]:
    """
    Extract function name from call expression node.
    
    Preconditions: node is valid tree-sitter Node
    Postconditions: returns function name or None
    """
    assert node is not None, "Node cannot be None"
    
    if node.type == 'identifier':
        return node.text.decode('utf-8')
    
    elif node.type == 'member_expression':
        property_node = node.child_by_field_name('property')
        if property_node and property_node.type == 'property_identifier':
            return property_node.text.decode('utf-8')
    
    return None
