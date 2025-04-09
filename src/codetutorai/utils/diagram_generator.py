"""
CodeTutorAI - Diagram Generator

This module provides functions for generating Mermaid diagrams from code.
"""

import os
import re
from typing import Any, Dict, List


def extract_classes(repo_dir: str, file_paths: List[str]) -> Dict[str, Dict]:
    """Extract class definitions from Python files.

    Args:
        repo_dir (str): The local path to the cloned repository.
        file_paths (list): List of relative file paths to analyze.

    Returns:
        dict: Dictionary mapping class names to class information
    """
    classes = {}

    # Regular expression for class definition
    class_pattern = r"class\s+(\w+)(?:\(([^)]*)\))?\s*:"
    method_pattern = r"def\s+(\w+)\s*\(self(?:,\s*[^)]*)?(?:\)\s*->.*?:|\):)"

    for rel_path in file_paths:
        if not rel_path.endswith(".py"):
            continue

        full_path = os.path.join(repo_dir, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            # Ignore files that cannot be read
            continue

        # Find all class definitions in the file
        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            parent_classes = class_match.group(2)

            # Extract parent classes
            parents = []
            if parent_classes:
                parents = [p.strip() for p in parent_classes.split(",")]

            # Find the class body
            class_start = class_match.end()
            class_body = content[class_start:]

            # Extract methods
            methods = []
            for method_match in re.finditer(method_pattern, class_body):
                method_name = method_match.group(1)
                if not method_name.startswith("_") or method_name in [
                    "__init__",
                    "__call__",
                ]:
                    methods.append(method_name)

            # Store class information
            classes[class_name] = {
                "file": rel_path, # Store relative path
                "parents": parents,
                "methods": methods,
            }

    return classes


def generate_class_diagram(classes: Dict[str, Dict]) -> str:
    """Generate a Mermaid class diagram from class information.

    Args:
        classes (dict): Dictionary mapping class names to class information

    Returns:
        str: Mermaid class diagram
    """
    diagram = ["```mermaid", "classDiagram"]

    # Add class definitions
    for class_name, info in classes.items():
        # Add inheritance relationships
        for parent in info["parents"]:
            if parent in classes:
                diagram.append(f"    {parent} <|-- {class_name}")

        # Add class with methods
        diagram.append(f"    class {class_name} {{")
        for method in info["methods"]:
            diagram.append(f"        +{method}()")
        diagram.append("    }")

    diagram.append("```")
    return "\n".join(diagram)


def extract_components(repo_dir: str, file_paths: List[str]) -> Dict[str, Dict]:
    """Extract component definitions from Python files.

    Args:
        repo_dir (str): The local path to the cloned repository.
        file_paths (list): List of relative file paths to analyze.

    Returns:
        dict: Dictionary mapping component names to component information
    """
    components = {}
    imports = {}

    # Regular expression for import statements
    import_pattern = r"from\s+([\w.]+)\s+import\s+([^#\n]+)"

    for rel_path in file_paths:
        if not rel_path.endswith(".py"):
            continue

        full_path = os.path.join(repo_dir, rel_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            # Ignore files that cannot be read
            continue

        # Extract the module name from the file path
        module_name = rel_path.replace(os.sep, ".").replace(".py", "")
        if module_name.startswith("."):
            module_name = module_name[1:]

        # Find all import statements in the file
        file_imports = []
        for import_match in re.finditer(import_pattern, content):
            module = import_match.group(1)
            imported = import_match.group(2)
            imported_items = [item.strip() for item in imported.split(",")]
            file_imports.extend([(module, item) for item in imported_items])

        # Store component information
        components[module_name] = {"file": rel_path, "imports": file_imports}

        # Store imports for dependency resolution
        imports[module_name] = file_imports

    # Resolve dependencies
    for component, info in components.items():
        dependencies = set()
        for module, item in info["imports"]:
            if module in components:
                dependencies.add(module)
        components[component]["dependencies"] = list(dependencies)

    return components


def generate_component_diagram(components: Dict[str, Dict]) -> str:
    """Generate a Mermaid component diagram from component information.

    Args:
        components (dict): Dictionary mapping component names to component information

    Returns:
        str: Mermaid component diagram
    """
    diagram = ["```mermaid", "flowchart TD"]

    # Add component definitions
    for component_name, info in components.items():
        # Simplify component name for display
        display_name = component_name.split(".")[-1]
        diagram.append(f"    {display_name}[{display_name}]")

    # Add dependencies
    for component_name, info in components.items():
        display_name = component_name.split(".")[-1]
        for dependency in info.get("dependencies", []):
            dep_display_name = dependency.split(".")[-1]
            diagram.append(f"    {dep_display_name} --> {display_name}")

    diagram.append("```")
    return "\n".join(diagram)


def generate_diagrams(repo_dir: str, abstractions: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, str]:
    """Generate Mermaid diagrams from code.

    Args:
        repo_dir (str): Local path to the cloned repository.
        abstractions (list): List of identified abstractions, used to find relevant files.
        verbose (bool): Whether to print verbose output.

    Returns:
        dict: Dictionary mapping diagram types to diagram content
    """
    # Extract all unique Python file paths from abstractions
    python_files = set()
    for abstraction in abstractions:
        for file_path in abstraction.get("files", []):
            if file_path.endswith(".py"):
                python_files.add(file_path)

    if verbose:
        print(f"Generating diagrams based on {len(python_files)} Python files.")

    if not python_files:
        return {
            "class_diagram": "```mermaid\nclassDiagram\n    %% No Python classes found\n```",
            "component_diagram": "```mermaid\nflowchart TD\n    %% No Python components found\n```",
        }

    python_file_list = list(python_files)
    classes = extract_classes(repo_dir, python_file_list)
    components = extract_components(repo_dir, python_file_list)

    diagrams = {
        "class_diagram": generate_class_diagram(classes),
        "component_diagram": generate_component_diagram(components),
    }

    return diagrams
