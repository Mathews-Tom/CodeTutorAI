"""
EnlightenAI - Analyze Relationships Node

This module contains the AnalyzeRelationshipsNode class for analyzing relationships
between abstractions in a codebase.
"""

import os
import json
from typing import Dict, List, Any, Set, Tuple

from enlightenai.nodes.node import Node
from enlightenai.utils.call_llm import call_llm


class AnalyzeRelationshipsNode(Node):
    """Node for analyzing relationships between abstractions in a codebase."""

    def process(self, context):
        """Analyze relationships between abstractions in a codebase.
        
        Args:
            context (dict): The shared context dictionary containing:
                - abstractions: List of abstractions
                - files: Dictionary of file contents
                - llm_provider: LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                
        Returns:
            dict: Dictionary containing relationships between abstractions.
        """
        verbose = context.get("verbose", False)
        llm_provider = context.get("llm_provider", "openai")
        api_key = context.get("api_key")
        
        # Get the abstractions
        abstractions = context.get("abstractions", [])
        
        if verbose:
            print(f"Analyzing relationships between {len(abstractions)} abstractions...")
        
        # Create a dictionary to store relationships
        relationships = {}
        
        # Analyze relationships between abstractions
        for i, abstraction in enumerate(abstractions):
            if verbose:
                print(f"Analyzing relationships for abstraction {i+1}/{len(abstractions)}: {abstraction['name']}")
            
            # Get the files for this abstraction
            abstraction_files = abstraction.get("files", [])
            
            # Find related abstractions
            related_abstractions = self._find_related_abstractions(
                abstraction, 
                abstractions, 
                context.get("files", {}),
                llm_provider,
                api_key,
                verbose
            )
            
            # Store the relationships
            relationships[abstraction["name"]] = related_abstractions
            
            if verbose:
                print(f"Found {len(related_abstractions)} related abstractions for {abstraction['name']}")
        
        if verbose:
            print("Relationship analysis complete!")
        
        return {"relationships": relationships}
    
    def _find_related_abstractions(
        self, 
        abstraction: Dict[str, Any], 
        abstractions: List[Dict[str, Any]], 
        files: Dict[str, str],
        llm_provider: str,
        api_key: str,
        verbose: bool
    ) -> List[str]:
        """Find abstractions related to the given abstraction.
        
        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions
            files (dict): Dictionary of file contents
            llm_provider (str): LLM provider to use
            api_key (str): API key for the LLM provider
            verbose (bool): Whether to print verbose output
            
        Returns:
            list: List of related abstraction names
        """
        # Get the files for this abstraction
        abstraction_files = abstraction.get("files", [])
        
        # Find direct imports and references in the files
        direct_relations = self._find_direct_relations(abstraction, abstractions, files)
        
        # Use LLM to find additional relationships
        llm_relations = self._find_llm_relations(abstraction, abstractions, files, llm_provider, api_key)
        
        # Combine the results
        related_abstractions = list(set(direct_relations + llm_relations))
        
        # Remove self-references
        if abstraction["name"] in related_abstractions:
            related_abstractions.remove(abstraction["name"])
        
        return related_abstractions
    
    def _find_direct_relations(
        self, 
        abstraction: Dict[str, Any], 
        abstractions: List[Dict[str, Any]], 
        files: Dict[str, str]
    ) -> List[str]:
        """Find direct relations between abstractions based on imports and references.
        
        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions
            files (dict): Dictionary of file contents
            
        Returns:
            list: List of related abstraction names
        """
        related_abstractions = []
        
        # Get the files for this abstraction
        abstraction_files = abstraction.get("files", [])
        
        # Create a mapping of file paths to abstractions
        file_to_abstraction = {}
        for a in abstractions:
            for file_path in a.get("files", []):
                file_to_abstraction[file_path] = a["name"]
        
        # Check for imports and references in the files
        for file_path in abstraction_files:
            if file_path not in files:
                continue
            
            file_content = files[file_path]
            
            # Check for imports
            import_lines = [line for line in file_content.split("\n") if line.strip().startswith(("import ", "from "))]
            
            for line in import_lines:
                # Extract the module name
                if line.strip().startswith("import "):
                    module_name = line.strip()[7:].split(" as ")[0].split(",")[0].strip()
                elif line.strip().startswith("from "):
                    module_name = line.strip()[5:].split(" import ")[0].strip()
                else:
                    continue
                
                # Check if the module is in any abstraction
                for a in abstractions:
                    if a["name"].lower() in module_name.lower() or module_name.lower() in a["name"].lower():
                        related_abstractions.append(a["name"])
            
            # Check for references to other abstractions
            for a in abstractions:
                if a["name"] == abstraction["name"]:
                    continue
                
                # Check if the abstraction name is mentioned in the file
                if a["name"].lower() in file_content.lower():
                    related_abstractions.append(a["name"])
        
        return list(set(related_abstractions))
    
    def _find_llm_relations(
        self, 
        abstraction: Dict[str, Any], 
        abstractions: List[Dict[str, Any]], 
        files: Dict[str, str],
        llm_provider: str,
        api_key: str
    ) -> List[str]:
        """Find relationships between abstractions using an LLM.
        
        Args:
            abstraction (dict): The abstraction to find related abstractions for
            abstractions (list): List of all abstractions
            files (dict): Dictionary of file contents
            llm_provider (str): LLM provider to use
            api_key (str): API key for the LLM provider
            
        Returns:
            list: List of related abstraction names
        """
        # Create a prompt for the LLM
        prompt = self._create_relationship_prompt(abstraction, abstractions)
        
        # Call the LLM
        response = call_llm(
            prompt, 
            provider=llm_provider, 
            api_key=api_key,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse the response
        related_abstractions = self._parse_llm_response(response, abstraction, abstractions)
        
        return related_abstractions
    
    def _create_relationship_prompt(
        self, 
        abstraction: Dict[str, Any], 
        abstractions: List[Dict[str, Any]]
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
Name: {abstraction['name']}
Description: {abstraction['description']}
Files: {', '.join(abstraction.get('files', []))}

# All Components in the Codebase
{json.dumps(abstraction_names, indent=2)}

# Task
Identify which components from the list above are likely related to the current component "{abstraction['name']}".
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
        abstractions: List[Dict[str, Any]]
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
                related_abstractions = [name for name in related_abstractions if name in abstraction_names]
                
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
