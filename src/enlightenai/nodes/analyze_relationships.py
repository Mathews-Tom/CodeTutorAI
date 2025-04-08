"""
EnlightenAI - Analyze Relationships Node

This module contains the AnalyzeRelationshipsNode class for analyzing relationships
between abstractions in a codebase.
"""

import ast
import json
import os
from typing import Any, Dict, List, Set, Tuple

from enlightenai.nodes.node import Node
from enlightenai.utils.llm_client import LLMClient  # Import the client class


class ImportVisitor(ast.NodeVisitor):
    """Node visitor to extract imports from an AST."""

    def __init__(self):
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])  # Get the top-level package
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            # Handle relative imports (level > 0) if necessary, for now focus on absolute
            if node.level == 0:
                self.imports.add(node.module.split(".")[0])  # Get the top-level package
        # We could also track specific names imported `from module import name1, name2`
        # but for component relationships, the module is often sufficient.
        self.generic_visit(node)

    # Optional: Add visit_Name, visit_Attribute to find potential references
    # This requires more complex logic to resolve scopes and aliases.
    # For now, we rely on the simpler string search below as a fallback.


class AnalyzeRelationshipsNode(Node):
    """Node for analyzing relationships between abstractions in a codebase."""

    def process(self, context):
        """Analyze relationships between abstractions in a codebase.

        Args:
            context (dict): The shared context dictionary containing:
                - abstractions: List of abstractions
                - file_paths: List of relative file paths in the repository
                - repo_dir: Local path to the cloned repository
                - llm_provider: LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                - cache_enabled: Whether to enable LLM caching
                - cache_dir: Directory for the LLM cache

        Returns:
            dict: Dictionary containing relationships between abstractions.
        """
        verbose = context.get("verbose", False)
        llm_provider = context.get("llm_provider", "openai")
        api_key = context.get("api_key")
        repo_dir = context.get("repo_dir")  # Needed for reading files
        cache_enabled = context.get("cache_enabled", False)
        cache_dir = context.get("cache_dir", ".llm_cache")
        # file_paths = context.get("file_paths", []) # Not directly used here, but available

        # Get the abstractions
        abstractions = context.get("abstractions", [])

        if verbose:
            print(
                f"Analyzing relationships between {len(abstractions)} abstractions..."
            )

        if not repo_dir:
            raise ValueError("repo_dir is required in the context to read files.")

        # Instantiate the LLM client with caching settings
        llm_client = LLMClient(
            provider=llm_provider,
            api_key=api_key,
            cache_enabled=cache_enabled,
            cache_dir=cache_dir,
            verbose=verbose,  # Pass verbose setting to client for cache logging
        )

        # Create a dictionary to store relationships
        relationships = {}

        # Analyze relationships between abstractions
        for i, abstraction in enumerate(abstractions):
            if verbose:
                print(
                    f"Analyzing relationships for abstraction {i + 1}/{len(abstractions)}: {abstraction['name']}"
                )

            # Find related abstractions
            related_abstractions = self._find_related_abstractions(
                abstraction,
                abstractions,
                repo_dir,
                llm_client,  # Pass the client instance
                verbose,
            )

            # Store the relationships
            relationships[abstraction["name"]] = related_abstractions

            if verbose:
                print(
                    f"Found {len(related_abstractions)} related abstractions for {abstraction['name']}"
                )

        if verbose:
            print("Relationship analysis complete!")

        return {"relationships": relationships}

    def _find_related_abstractions(
        self,
        abstraction: Dict[str, Any],
        abstractions: List[Dict[str, Any]],
        repo_dir: str,
        llm_client: LLMClient,  # Changed parameters
        verbose: bool,
    ) -> List[str]:
        """Find abstractions related to the given abstraction.

        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions
            repo_dir (str): Local path to the cloned repository
            llm_client (LLMClient): The LLM client instance
            verbose (bool): Whether to print verbose output

        Returns:
            list: List of related abstraction names
        """
        # Find direct imports and references in the files
        direct_relations = self._find_direct_relations(
            abstraction, abstractions, repo_dir, verbose
        )

        # Use LLM to find additional relationships (Temporarily disabled for performance)
        # llm_relations = self._find_llm_relations(
        #     abstraction, abstractions, llm_client
        # )
        llm_relations = []  # Ensure llm_relations is an empty list if disabled

        # Combine the results (currently only direct relations)
        related_abstractions = list(
            set(direct_relations + llm_relations)
        )  # Keep structure for potential re-enabling

        # Remove self-references
        if abstraction["name"] in related_abstractions:
            related_abstractions.remove(abstraction["name"])

        return related_abstractions

    def _find_direct_relations(
        self,
        abstraction: Dict[str, Any],
        abstractions: List[Dict[str, Any]],
        repo_dir: str,
        verbose: bool,
    ) -> List[str]:
        """Find direct relations between abstractions based on imports and references.

        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions
            repo_dir (str): Local path to the cloned repository
            verbose (bool): Whether to print verbose output

        Returns:
            list: List of related abstraction names
        """
        related_abstractions = set()  # Use a set to avoid duplicates initially
        processed_py_file = False  # Track if we processed any Python files
        processed_content = False  # Flag to avoid reading content if not needed

        # Get the files for this abstraction
        abstraction_files = abstraction.get("files", [])

        # Create a mapping of file paths to abstractions
        file_to_abstraction = {}
        for a in abstractions:
            for file_path in a.get("files", []):
                file_to_abstraction[file_path] = a["name"]

        # Create a mapping of lower-case abstraction names to original names
        # This helps in case-insensitive matching later
        lower_to_orig_abstraction = {a["name"].lower(): a["name"] for a in abstractions}

        # Check for imports and references in the files
        for file_path in abstraction_files:
            full_path = os.path.join(repo_dir, file_path)
            if not os.path.exists(full_path):
                if verbose:
                    print(f"  Warning: File not found for direct analysis: {full_path}")
                continue

            # Read file content on demand
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()
                processed_content = True
            except Exception as e:
                if verbose:
                    print(f"  Warning: Could not read file {full_path}: {e}")
                continue

            # --- AST Analysis for Python files ---
            if file_path.endswith(".py"):
                processed_py_file = True
                try:
                    tree = ast.parse(file_content, filename=file_path)
                    visitor = ImportVisitor()
                    visitor.visit(tree)

                    # Check if imported modules correspond to other abstractions
                    for imported_module in visitor.imports:
                        # This matching is basic, might need refinement based on project structure
                        # e.g., check if 'enlightenai.nodes.node' matches 'Node' abstraction
                        for (
                            abs_name_lower,
                            abs_name_orig,
                        ) in lower_to_orig_abstraction.items():
                            # Check if import matches start of an abstraction name or vice-versa (simple check)
                            if abs_name_lower.startswith(
                                imported_module.lower()
                            ) or imported_module.lower().startswith(abs_name_lower):
                                if (
                                    abs_name_orig != abstraction["name"]
                                ):  # Avoid self-relation
                                    related_abstractions.add(abs_name_orig)

                except SyntaxError as e:
                    if verbose:
                        print(
                            f"  Warning: Could not parse Python file {file_path}: {e}"
                        )
                except Exception as e:  # Catch other potential AST errors
                    if verbose:
                        print(f"  Warning: Error processing AST for {file_path}: {e}")

            # --- Fallback: Simple String Search for References (kept for now) ---
            # This is less reliable but catches mentions not found via imports/AST
            for abs_name_lower, abs_name_orig in lower_to_orig_abstraction.items():
                if (
                    abs_name_orig != abstraction["name"]
                    and abs_name_lower in file_content.lower()
                ):
                    related_abstractions.add(abs_name_orig)

        return list(related_abstractions)

    def _find_llm_relations(
        self,
        abstraction: Dict[str, Any],
        abstractions: List[Dict[str, Any]],
        llm_client: LLMClient,  # Changed from provider/key
    ) -> List[str]:
        """Find relationships between abstractions using an LLM.

        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions
            llm_client (LLMClient): The LLM client instance

        Returns:
            list: List of related abstraction names
        """
        # Create a prompt for the LLM
        prompt = self._create_relationship_prompt(abstraction, abstractions)

        # Call the LLM
        response = llm_client.call(  # Use the client instance
            prompt,
            # provider and api_key are handled by the client instance
            max_tokens=1000,
            temperature=0.7,
        )

        # Parse the response
        related_abstractions = self._parse_llm_response(
            response, abstraction, abstractions
        )

        return related_abstractions

    def _create_relationship_prompt(
        self, abstraction: Dict[str, Any], abstractions: List[Dict[str, Any]]
    ) -> str:
        """Create a prompt for the LLM to find relationships between abstractions.

        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions

        Returns:
            str: The prompt for the LLM
        """
        # Create a list of abstraction names
        abstraction_names = [a["name"] for a in abstractions]

        # Create the prompt
        prompt = f"""
You are an expert software architect analyzing relationships between components in a codebase.

# Current Component
Name: {abstraction["name"]}
Description: {abstraction["description"]}
Files: {", ".join(abstraction.get("files", []))}

# All Components in the Codebase
{json.dumps(abstraction_names, indent=2)}

# Task
Identify which components from the list above are likely related to the current component "{abstraction["name"]}".
Consider:
1. Dependencies (the current component might use other components)
2. Dependents (other components might use the current component)
3. Shared functionality or domain concepts
4. Architectural relationships (e.g., part of the same subsystem)

# Output Format
Return a JSON array of component names that are related to the current component.
Example: ["ComponentA", "ComponentB", "ComponentC"]

Only include components that have a meaningful relationship with the current component.
"""

        return prompt

    def _parse_llm_response(
        self,
        response: str,
        abstraction: Dict[str, Any],
        abstractions: List[Dict[str, Any]],
    ) -> List[str]:
        """Parse the LLM response to extract related abstraction names.

        Args:
            response (str): The LLM response
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions

        Returns:
            list: List of related abstraction names
        """
        # Create a list of abstraction names
        abstraction_names = [a["name"] for a in abstractions]

        # Try to parse the response as JSON
        try:
            # Find the JSON array in the response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                related_abstractions = json.loads(json_str)

                # Filter out invalid abstraction names
                related_abstractions = [
                    name for name in related_abstractions if name in abstraction_names
                ]

                return related_abstractions
        except Exception:
            pass

        # If JSON parsing fails, try to extract abstraction names from the response
        related_abstractions = []

        for name in abstraction_names:
            if name == abstraction["name"]:
                continue

            if name in response:
                related_abstractions.append(name)

        return related_abstractions
