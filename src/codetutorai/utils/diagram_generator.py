"""
CodeTutorAI - Diagram Generator

This module provides functions for generating Mermaid diagrams from code.
"""

import os
import re
from typing import Any, Dict, List

from .formatting import sanitize_mermaid_label # Added import


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

    # Pass 1: Define all class blocks and their methods
    defined_classes = {} # Map original name to sanitized name for valid classes
    for class_name, info in classes.items():
        sanitized_class_name = sanitize_mermaid_label(class_name)
        # Ensure the sanitized name is valid and unique before defining the block
        if sanitized_class_name and sanitized_class_name not in defined_classes.values():
            defined_classes[class_name] = sanitized_class_name
            diagram.append(f"    class {sanitized_class_name} {{")
            for method in info["methods"]:
                sanitized_method_name = sanitize_mermaid_label(method)
                if sanitized_method_name: # Ensure method name is valid
                    # Remove explicit '+' for public methods, simplifying syntax
                    diagram.append(f"        {sanitized_method_name}()")
            diagram.append("    }")
        elif not sanitized_class_name:
             print(f"Warning: Skipping class '{class_name}' due to invalid sanitized name.") # Optional: Add logging/warning
        # If sanitized_class_name is already in defined_classes.values(), it's a duplicate after sanitization, skip block definition


    # Pass 2: Define all inheritance relationships, avoiding duplicates
    added_relationships = set() # Track added relationships as (parent_sanitized, child_sanitized) tuples
    for class_name, info in classes.items():
        child_sanitized = defined_classes.get(class_name)
        if not child_sanitized: # Skip if the child class wasn't validly defined
            continue

        for parent in info["parents"]:
            parent_sanitized = defined_classes.get(parent)
            if parent_sanitized: # Ensure parent was also validly defined
                relationship = (parent_sanitized, child_sanitized)
                if relationship not in added_relationships:
                    diagram.append(f"    {parent_sanitized} <|-- {child_sanitized}")
                    added_relationships.add(relationship)

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
    component_ids = {} # Map original name to sanitized ID
    processed_ids = set() # Track processed sanitized IDs

    for component_name in components.keys():
        # Simplify component name for display and sanitize it for use as ID
        display_name = component_name.split(".")[-1]
        sanitized_id = sanitize_mermaid_label(display_name)
        if not sanitized_id or sanitized_id in processed_ids:
            # Handle empty or duplicate sanitized IDs (e.g., skip or generate unique)
            # For now, we map the original name but might skip adding the node if ID conflicts
            component_ids[component_name] = None # Mark as problematic
            continue
        component_ids[component_name] = sanitized_id
        processed_ids.add(sanitized_id)
        # Use the sanitized ID for the node ID, keep original-like display name for label
        diagram.append(f'    {sanitized_id}["{display_name}"]') # Use quotes for label

    # Add dependencies using sanitized IDs
    for component_name, info in components.items():
        source_id = component_ids.get(component_name)
        if not source_id: # Skip if source node was problematic
            continue

        for dependency in info.get("dependencies", []):
            target_id = component_ids.get(dependency)
            if target_id: # Ensure target node exists and is valid
                diagram.append(f"    {target_id} --> {source_id}") # Arrow from dependency to component

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
