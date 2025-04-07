"""
EnlightenAI - Code Analysis Utilities

This module provides utilities for analyzing code files, including language detection,
structure extraction, and other code analysis functions.
"""

import re
import os
from typing import Dict, List, Any, Optional, Tuple


def detect_language(file_path: str) -> str:
    """Detect the programming language of a file based on its extension.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: The detected programming language
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.rs': 'rust',
        '.scala': 'scala',
        '.m': 'objective-c',
        '.mm': 'objective-c',
        '.pl': 'perl',
        '.sh': 'bash',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.md': 'markdown',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sql': 'sql',
        '.r': 'r',
        '.dart': 'dart',
        '.lua': 'lua',
        '.ex': 'elixir',
        '.exs': 'elixir',
        '.erl': 'erlang',
        '.hrl': 'erlang',
        '.clj': 'clojure',
        '.hs': 'haskell',
        '.fs': 'fsharp',
        '.fsx': 'fsharp',
    }
    
    return language_map.get(ext, 'unknown')


def extract_code_structure(file_path: str, content: str, language: Optional[str] = None) -> Dict[str, Any]:
    """Extract the structure of a code file.
    
    Args:
        file_path (str): Path to the file
        content (str): Content of the file
        language (str, optional): Programming language of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    if language is None:
        language = detect_language(file_path)
    
    # Use language-specific extractors
    if language == 'python':
        return extract_python_structure(content)
    elif language in ['javascript', 'typescript']:
        return extract_js_ts_structure(content)
    elif language == 'java':
        return extract_java_structure(content)
    elif language in ['c', 'cpp']:
        return extract_c_cpp_structure(content)
    elif language == 'go':
        return extract_go_structure(content)
    else:
        # Generic structure extraction for unsupported languages
        return extract_generic_structure(content)


def extract_python_structure(content: str) -> Dict[str, Any]:
    """Extract the structure of a Python file.
    
    Args:
        content (str): Content of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    structure = {
        'imports': [],
        'classes': [],
        'functions': [],
        'variables': []
    }
    
    # Extract imports
    import_pattern = r'^(?:import|from)\s+([^\s]+)(?:\s+import\s+([^#\n]+))?'
    for match in re.finditer(import_pattern, content, re.MULTILINE):
        if match.group(2):  # from X import Y
            module = match.group(1)
            imports = [imp.strip() for imp in match.group(2).split(',')]
            for imp in imports:
                structure['imports'].append(f"from {module} import {imp}")
        else:  # import X
            structure['imports'].append(f"import {match.group(1)}")
    
    # Extract classes
    class_pattern = r'class\s+([^\s(:]+)(?:\(([^)]+)\))?:'
    for match in re.finditer(class_pattern, content, re.MULTILINE):
        class_name = match.group(1)
        parent_classes = []
        if match.group(2):
            parent_classes = [p.strip() for p in match.group(2).split(',')]
        
        # Find class methods
        class_start = match.start()
        next_class = re.search(class_pattern, content[class_start + 1:], re.MULTILINE)
        class_end = next_class.start() + class_start + 1 if next_class else len(content)
        class_content = content[class_start:class_end]
        
        # Extract methods
        methods = []
        method_pattern = r'def\s+([^\s(]+)\s*\(([^)]*)\)'
        for method_match in re.finditer(method_pattern, class_content, re.MULTILINE):
            method_name = method_match.group(1)
            params = method_match.group(2).strip()
            methods.append({
                'name': method_name,
                'params': params
            })
        
        structure['classes'].append({
            'name': class_name,
            'parents': parent_classes,
            'methods': methods
        })
    
    # Extract standalone functions
    function_pattern = r'^def\s+([^\s(]+)\s*\(([^)]*)\)'
    for match in re.finditer(function_pattern, content, re.MULTILINE):
        function_name = match.group(1)
        params = match.group(2).strip()
        structure['functions'].append({
            'name': function_name,
            'params': params
        })
    
    # Extract top-level variables
    variable_pattern = r'^([A-Z_][A-Z0-9_]*)\s*='
    for match in re.finditer(variable_pattern, content, re.MULTILINE):
        structure['variables'].append(match.group(1))
    
    return structure


def extract_js_ts_structure(content: str) -> Dict[str, Any]:
    """Extract the structure of a JavaScript or TypeScript file.
    
    Args:
        content (str): Content of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    structure = {
        'imports': [],
        'classes': [],
        'functions': [],
        'variables': []
    }
    
    # Extract imports
    import_pattern = r'(?:import|require)\s+([^;]+)'
    for match in re.finditer(import_pattern, content, re.MULTILINE):
        structure['imports'].append(match.group(1).strip())
    
    # Extract classes
    class_pattern = r'class\s+([^\s{]+)(?:\s+extends\s+([^\s{]+))?'
    for match in re.finditer(class_pattern, content, re.MULTILINE):
        class_name = match.group(1)
        parent_class = match.group(2) if match.group(2) else None
        
        # Find class methods
        class_start = match.start()
        class_block_start = content.find('{', class_start)
        if class_block_start == -1:
            continue
        
        # Find matching closing brace
        brace_count = 1
        class_end = class_block_start + 1
        while brace_count > 0 and class_end < len(content):
            if content[class_end] == '{':
                brace_count += 1
            elif content[class_end] == '}':
                brace_count -= 1
            class_end += 1
        
        class_content = content[class_block_start:class_end]
        
        # Extract methods
        methods = []
        method_pattern = r'(?:async\s+)?(?:function\s+)?([^\s(]+)\s*\(([^)]*)\)'
        for method_match in re.finditer(method_pattern, class_content, re.MULTILINE):
            method_name = method_match.group(1)
            params = method_match.group(2).strip()
            methods.append({
                'name': method_name,
                'params': params
            })
        
        structure['classes'].append({
            'name': class_name,
            'parent': parent_class,
            'methods': methods
        })
    
    # Extract standalone functions
    function_pattern = r'(?:function|const|let|var)\s+([^\s(=]+)\s*(?:=\s*(?:async\s*)?\([^)]*\)\s*=>|[=\(])'
    for match in re.finditer(function_pattern, content, re.MULTILINE):
        function_name = match.group(1)
        structure['functions'].append({
            'name': function_name
        })
    
    # Extract top-level variables
    variable_pattern = r'(?:const|let|var)\s+([A-Z_][A-Z0-9_]*)\s*='
    for match in re.finditer(variable_pattern, content, re.MULTILINE):
        structure['variables'].append(match.group(1))
    
    return structure


def extract_java_structure(content: str) -> Dict[str, Any]:
    """Extract the structure of a Java file.
    
    Args:
        content (str): Content of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    structure = {
        'imports': [],
        'package': None,
        'classes': [],
        'interfaces': []
    }
    
    # Extract package
    package_pattern = r'package\s+([^;]+);'
    package_match = re.search(package_pattern, content)
    if package_match:
        structure['package'] = package_match.group(1).strip()
    
    # Extract imports
    import_pattern = r'import\s+([^;]+);'
    for match in re.finditer(import_pattern, content, re.MULTILINE):
        structure['imports'].append(match.group(1).strip())
    
    # Extract classes
    class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+([^\s{<]+)(?:<[^>]+>)?(?:\s+extends\s+([^\s{<]+)(?:<[^>]+>)?)?(?:\s+implements\s+([^{]+))?'
    for match in re.finditer(class_pattern, content, re.MULTILINE):
        class_name = match.group(1)
        parent_class = match.group(2) if match.group(2) else None
        interfaces = []
        if match.group(3):
            interfaces = [i.strip() for i in match.group(3).split(',')]
        
        structure['classes'].append({
            'name': class_name,
            'parent': parent_class,
            'interfaces': interfaces
        })
    
    # Extract interfaces
    interface_pattern = r'(?:public|private|protected)?\s*interface\s+([^\s{<]+)(?:<[^>]+>)?(?:\s+extends\s+([^{]+))?'
    for match in re.finditer(interface_pattern, content, re.MULTILINE):
        interface_name = match.group(1)
        parent_interfaces = []
        if match.group(2):
            parent_interfaces = [i.strip() for i in match.group(2).split(',')]
        
        structure['interfaces'].append({
            'name': interface_name,
            'parents': parent_interfaces
        })
    
    return structure


def extract_c_cpp_structure(content: str) -> Dict[str, Any]:
    """Extract the structure of a C/C++ file.
    
    Args:
        content (str): Content of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    structure = {
        'includes': [],
        'defines': [],
        'classes': [],
        'structs': [],
        'functions': []
    }
    
    # Extract includes
    include_pattern = r'#include\s+[<"]([^>"]+)[>"]'
    for match in re.finditer(include_pattern, content, re.MULTILINE):
        structure['includes'].append(match.group(1))
    
    # Extract defines
    define_pattern = r'#define\s+([^\s(]+)'
    for match in re.finditer(define_pattern, content, re.MULTILINE):
        structure['defines'].append(match.group(1))
    
    # Extract classes (C++)
    class_pattern = r'(?:class|struct)\s+([^\s:;{]+)(?:\s*:\s*(?:public|protected|private)\s+([^{]+))?'
    for match in re.finditer(class_pattern, content, re.MULTILINE):
        class_name = match.group(1)
        parent_classes = []
        if match.group(2):
            parent_classes = [p.strip() for p in match.group(2).split(',')]
        
        if 'class' in match.group(0):
            structure['classes'].append({
                'name': class_name,
                'parents': parent_classes
            })
        else:
            structure['structs'].append({
                'name': class_name,
                'parents': parent_classes
            })
    
    # Extract functions
    function_pattern = r'(?:static|inline|extern)?\s*(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*0)?\s*(?:{\s*)?'
    for match in re.finditer(function_pattern, content, re.MULTILINE):
        function_name = match.group(1)
        params = match.group(2).strip()
        
        # Skip if this is likely a variable declaration
        if function_name in ['if', 'for', 'while', 'switch', 'return']:
            continue
        
        structure['functions'].append({
            'name': function_name,
            'params': params
        })
    
    return structure


def extract_go_structure(content: str) -> Dict[str, Any]:
    """Extract the structure of a Go file.
    
    Args:
        content (str): Content of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    structure = {
        'package': None,
        'imports': [],
        'structs': [],
        'interfaces': [],
        'functions': []
    }
    
    # Extract package
    package_pattern = r'package\s+([^\s]+)'
    package_match = re.search(package_pattern, content)
    if package_match:
        structure['package'] = package_match.group(1)
    
    # Extract imports
    import_block_pattern = r'import\s+\(\s*(.*?)\s*\)'
    import_block_match = re.search(import_block_pattern, content, re.DOTALL)
    if import_block_match:
        import_lines = import_block_match.group(1).strip().split('\n')
        for line in import_lines:
            line = line.strip()
            if line and not line.startswith('//'):
                structure['imports'].append(line.strip('"'))
    else:
        # Single import
        import_pattern = r'import\s+"([^"]+)"'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            structure['imports'].append(match.group(1))
    
    # Extract structs
    struct_pattern = r'type\s+([^\s]+)\s+struct\s+{([^}]*)}'
    for match in re.finditer(struct_pattern, content, re.DOTALL):
        struct_name = match.group(1)
        fields_text = match.group(2).strip()
        fields = []
        
        if fields_text:
            field_lines = fields_text.split('\n')
            for line in field_lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    fields.append(line)
        
        structure['structs'].append({
            'name': struct_name,
            'fields': fields
        })
    
    # Extract interfaces
    interface_pattern = r'type\s+([^\s]+)\s+interface\s+{([^}]*)}'
    for match in re.finditer(interface_pattern, content, re.DOTALL):
        interface_name = match.group(1)
        methods_text = match.group(2).strip()
        methods = []
        
        if methods_text:
            method_lines = methods_text.split('\n')
            for line in method_lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    methods.append(line)
        
        structure['interfaces'].append({
            'name': interface_name,
            'methods': methods
        })
    
    # Extract functions
    function_pattern = r'func\s+(?:\([^)]+\)\s+)?([^\s(]+)\s*\(([^)]*)\)'
    for match in re.finditer(function_pattern, content, re.MULTILINE):
        function_name = match.group(1)
        params = match.group(2).strip()
        structure['functions'].append({
            'name': function_name,
            'params': params
        })
    
    return structure


def extract_generic_structure(content: str) -> Dict[str, Any]:
    """Extract a generic structure from a code file.
    
    Args:
        content (str): Content of the file
            
    Returns:
        dict: Dictionary containing the extracted structure
    """
    structure = {
        'imports': [],
        'classes': [],
        'functions': [],
        'variables': []
    }
    
    # Generic import patterns
    import_patterns = [
        r'import\s+([^;]+)',
        r'#include\s+[<"]([^>"]+)[>"]',
        r'require\s+[\'"]([^\'"]+)[\'"]',
        r'using\s+([^;]+)'
    ]
    
    for pattern in import_patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            structure['imports'].append(match.group(1).strip())
    
    # Generic class patterns
    class_patterns = [
        r'class\s+([^\s{:]+)',
        r'interface\s+([^\s{:]+)',
        r'struct\s+([^\s{:]+)',
        r'type\s+([^\s]+)\s+struct',
        r'type\s+([^\s]+)\s+interface'
    ]
    
    for pattern in class_patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            structure['classes'].append({
                'name': match.group(1)
            })
    
    # Generic function patterns
    function_patterns = [
        r'function\s+([^\s(]+)',
        r'def\s+([^\s(:]+)',
        r'func\s+([^\s(]+)',
        r'sub\s+([^\s(]+)',
        r'void\s+([^\s(]+)',
        r'int\s+([^\s(]+)',
        r'string\s+([^\s(]+)',
        r'bool\s+([^\s(]+)',
        r'double\s+([^\s(]+)',
        r'float\s+([^\s(]+)'
    ]
    
    for pattern in function_patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            function_name = match.group(1)
            # Skip if this is likely a variable declaration
            if function_name in ['if', 'for', 'while', 'switch', 'return']:
                continue
            structure['functions'].append({
                'name': function_name
            })
    
    return structure


def chunk_codebase(files: Dict[str, str], max_chunk_size: int = 5000) -> List[Dict[str, Any]]:
    """Chunk a codebase into smaller pieces for analysis.
    
    Args:
        files (dict): Dictionary mapping file paths to file contents
        max_chunk_size (int, optional): Maximum size of each chunk in characters
            
    Returns:
        list: List of chunks, where each chunk is a dictionary with file paths and contents
    """
    chunks = []
    current_chunk = {}
    current_size = 0
    
    for path, content in files.items():
        content_size = len(content)
        
        # If the file is larger than max_chunk_size, split it
        if content_size > max_chunk_size:
            # Add the current chunk if it's not empty
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = {}
                current_size = 0
            
            # Split the large file into chunks
            for i in range(0, content_size, max_chunk_size):
                chunk_content = content[i:i + max_chunk_size]
                chunks.append({
                    f"{path} (part {i // max_chunk_size + 1})": chunk_content
                })
        
        # If adding this file would exceed max_chunk_size, start a new chunk
        elif current_size + content_size > max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = {path: content}
            current_size = content_size
        
        # Otherwise, add the file to the current chunk
        else:
            current_chunk[path] = content
            current_size += content_size
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def group_files_by_language(files: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """Group files by programming language.
    
    Args:
        files (dict): Dictionary mapping file paths to file contents
            
    Returns:
        dict: Dictionary mapping language names to dictionaries of files
    """
    language_groups = {}
    
    for path, content in files.items():
        language = detect_language(path)
        
        if language not in language_groups:
            language_groups[language] = {}
        
        language_groups[language][path] = content
    
    return language_groups


def analyze_codebase_structure(files: Dict[str, str]) -> Dict[str, Any]:
    """Analyze the structure of a codebase.
    
    Args:
        files (dict): Dictionary mapping file paths to file contents
            
    Returns:
        dict: Dictionary containing the analyzed structure
    """
    structure = {
        'languages': {},
        'files_by_language': {},
        'abstractions': {
            'classes': [],
            'functions': [],
            'interfaces': [],
            'structs': []
        },
        'dependencies': {}
    }
    
    # Group files by language
    language_groups = group_files_by_language(files)
    structure['files_by_language'] = {lang: list(files.keys()) for lang, files in language_groups.items()}
    
    # Count files by language
    structure['languages'] = {lang: len(files) for lang, files in language_groups.items()}
    
    # Extract structure from each file
    for path, content in files.items():
        language = detect_language(path)
        file_structure = extract_code_structure(path, content, language)
        
        # Add classes to abstractions
        if 'classes' in file_structure:
            for cls in file_structure['classes']:
                cls['file'] = path
                cls['language'] = language
                structure['abstractions']['classes'].append(cls)
        
        # Add functions to abstractions
        if 'functions' in file_structure:
            for func in file_structure['functions']:
                func['file'] = path
                func['language'] = language
                structure['abstractions']['functions'].append(func)
        
        # Add interfaces to abstractions
        if 'interfaces' in file_structure:
            for interface in file_structure['interfaces']:
                interface['file'] = path
                interface['language'] = language
                structure['abstractions']['interfaces'].append(interface)
        
        # Add structs to abstractions
        if 'structs' in file_structure:
            for struct in file_structure['structs']:
                struct['file'] = path
                struct['language'] = language
                structure['abstractions']['structs'].append(struct)
        
        # Extract dependencies
        if 'imports' in file_structure:
            structure['dependencies'][path] = file_structure['imports']
        elif 'includes' in file_structure:
            structure['dependencies'][path] = file_structure['includes']
    
    return structure
