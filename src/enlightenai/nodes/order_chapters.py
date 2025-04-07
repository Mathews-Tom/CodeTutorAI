"""
EnlightenAI - Order Chapters Node

This module contains the OrderChaptersNode class for ordering tutorial chapters.
"""

import os
import json
from typing import Dict, List, Any, Set, Tuple

from enlightenai.nodes.node import Node
from enlightenai.utils.call_llm import call_llm


class OrderChaptersNode(Node):
    """Node for ordering tutorial chapters."""

    def process(self, context):
        """Order tutorial chapters based on dependencies and learning curve.
        
        Args:
            context (dict): The shared context dictionary containing:
                - abstractions: List of abstractions
                - relationships: Dictionary of relationships between abstractions
                - repo_name: Name of the repository
                - output_dir: Output directory for the tutorial
                - ordering_method: Method to use for ordering chapters
                - llm_provider: LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                
        Returns:
            dict: Dictionary containing the ordered chapters.
        """
        verbose = context.get("verbose", False)
        abstractions = context.get("abstractions", [])
        relationships = context.get("relationships", {})
        repo_name = context.get("repo_name", "")
        output_dir = context.get("output_dir", "tutorial_output")
        ordering_method = context.get("ordering_method", "auto")
        llm_provider = context.get("llm_provider", "openai")
        api_key = context.get("api_key")
        
        if verbose:
            print(f"Ordering {len(abstractions)} chapters using method: {ordering_method}")
        
        # Order the chapters based on the specified method
        if ordering_method == "topological":
            ordered_chapters = self._order_topological(abstractions, relationships, verbose)
        elif ordering_method == "learning_curve":
            ordered_chapters = self._order_learning_curve(abstractions, relationships, verbose)
        elif ordering_method == "llm":
            ordered_chapters = self._order_llm(abstractions, relationships, repo_name, llm_provider, api_key, verbose)
        else:  # auto
            # Try topological ordering first, then fall back to learning curve
            ordered_chapters = self._order_topological(abstractions, relationships, verbose)
            if not ordered_chapters:
                ordered_chapters = self._order_learning_curve(abstractions, relationships, verbose)
        
        if verbose:
            print(f"Ordered chapters: {ordered_chapters}")
        
        # Save the ordered chapters to a file
        ordered_chapters_path = os.path.join(output_dir, "ordered_chapters.json")
        with open(ordered_chapters_path, "w", encoding="utf-8") as f:
            json.dump(ordered_chapters, f, indent=2)
        
        if verbose:
            print(f"Saved ordered chapters to {ordered_chapters_path}")
        
        # Update the context
        return {"ordered_chapters": ordered_chapters}
    
    def _order_topological(
        self, 
        abstractions: List[Dict[str, Any]], 
        relationships: Dict[str, List[str]], 
        verbose: bool
    ) -> List[str]:
        """Order chapters using topological sorting based on dependencies.
        
        Args:
            abstractions (list): List of abstractions
            relationships (dict): Dictionary of relationships between abstractions
            verbose (bool): Whether to print verbose output
            
        Returns:
            list: List of ordered chapter titles
        """
        if verbose:
            print("Using topological ordering")
        
        # Create a graph of dependencies
        graph = {}
        for abstraction in abstractions:
            name = abstraction["name"]
            graph[name] = set(relationships.get(name, []))
        
        # Perform topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(node):
            if node in temp_visited:
                # Cycle detected
                return False
            if node in visited:
                return True
            
            temp_visited.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in graph and not visit(neighbor):
                    return False
            
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)
            return True
        
        # Visit each node
        for node in graph:
            if node not in visited:
                if not visit(node):
                    # Cycle detected, topological sort not possible
                    if verbose:
                        print("Cycle detected, topological sort not possible")
                    return []
        
        # Reverse the order to get the correct topological sort
        order.reverse()
        
        return order
    
    def _order_learning_curve(
        self, 
        abstractions: List[Dict[str, Any]], 
        relationships: Dict[str, List[str]], 
        verbose: bool
    ) -> List[str]:
        """Order chapters based on learning curve (simpler concepts first).
        
        Args:
            abstractions (list): List of abstractions
            relationships (dict): Dictionary of relationships between abstractions
            verbose (bool): Whether to print verbose output
            
        Returns:
            list: List of ordered chapter titles
        """
        if verbose:
            print("Using learning curve ordering")
        
        # Calculate the complexity of each abstraction based on its relationships
        complexity = {}
        for abstraction in abstractions:
            name = abstraction["name"]
            # Complexity is based on the number of relationships and files
            num_relationships = len(relationships.get(name, []))
            num_files = len(abstraction.get("files", []))
            complexity[name] = num_relationships + num_files
        
        # Sort abstractions by complexity
        ordered_chapters = sorted([a["name"] for a in abstractions], key=lambda name: complexity.get(name, 0))
        
        return ordered_chapters
    
    def _order_llm(
        self, 
        abstractions: List[Dict[str, Any]], 
        relationships: Dict[str, List[str]], 
        repo_name: str,
        llm_provider: str,
        api_key: str,
        verbose: bool
    ) -> List[str]:
        """Order chapters using an LLM to determine the best learning sequence.
        
        Args:
            abstractions (list): List of abstractions
            relationships (dict): Dictionary of relationships between abstractions
            repo_name (str): Name of the repository
            llm_provider (str): LLM provider to use
            api_key (str): API key for the LLM provider
            verbose (bool): Whether to print verbose output
            
        Returns:
            list: List of ordered chapter titles
        """
        if verbose:
            print("Using LLM-based ordering")
        
        # Create a prompt for the LLM
        prompt = self._create_ordering_prompt(abstractions, relationships, repo_name)
        
        # Call the LLM
        response = call_llm(
            prompt, 
            provider=llm_provider, 
            api_key=api_key,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Parse the response
        ordered_chapters = self._parse_ordering_response(response, abstractions)
        
        return ordered_chapters
    
    def _create_ordering_prompt(
        self, 
        abstractions: List[Dict[str, Any]], 
        relationships: Dict[str, List[str]], 
        repo_name: str
    ) -> str:
        """Create a prompt for the LLM to order chapters.
        
        Args:
            abstractions (list): List of abstractions
            relationships (dict): Dictionary of relationships between abstractions
            repo_name (str): Name of the repository
            
        Returns:
            str: The prompt for the LLM
        """
        # Create a summary of the abstractions
        abstractions_summary = ""
        for i, abstraction in enumerate(abstractions):
            abstractions_summary += f"{i+1}. {abstraction['name']}: {abstraction['description']}\n"
        
        # Create a summary of the relationships
        relationships_summary = ""
        for name, related in relationships.items():
            if related:
                relationships_summary += f"{name} -> {', '.join(related)}\n"
        
        # Create the prompt
        prompt = f"""
You are an expert software architect and technical writer. Your task is to determine the optimal order for chapters in a tutorial about the {repo_name} codebase.

# Abstractions (Potential Chapters)
{abstractions_summary}

# Relationships Between Abstractions
{relationships_summary}

# Task
Determine the optimal order for these abstractions to be presented as chapters in a tutorial. Consider:
1. Dependencies between abstractions (dependent abstractions should come after their dependencies)
2. Learning curve (simpler concepts should come before more complex ones)
3. Logical flow (the tutorial should have a natural progression)

# Output Format
Return a JSON array of abstraction names in the optimal order.
Example: ["Introduction", "BasicConcepts", "CoreComponents", "AdvancedFeatures"]

Ensure that all abstractions are included in the output.
"""
        
        return prompt
    
    def _parse_ordering_response(self, response: str, abstractions: List[Dict[str, Any]]) -> List[str]:
        """Parse the LLM response to extract the ordered chapters.
        
        Args:
            response (str): The LLM response
            abstractions (list): List of abstractions
            
        Returns:
            list: List of ordered chapter titles
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
                ordered_chapters = json.loads(json_str)
                
                # Validate the ordered chapters
                valid_chapters = []
                for chapter in ordered_chapters:
                    if chapter in abstraction_names:
                        valid_chapters.append(chapter)
                
                # Add any missing abstractions to the end
                for name in abstraction_names:
                    if name not in valid_chapters:
                        valid_chapters.append(name)
                
                return valid_chapters
        except Exception:
            pass
        
        # If JSON parsing fails, fall back to the original order
        return abstraction_names
