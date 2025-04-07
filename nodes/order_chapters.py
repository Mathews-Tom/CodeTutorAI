"""
EnlightenAI - Order Chapters Node

This module contains the OrderChaptersNode class, which is responsible for
determining the logical order of chapters in the tutorial.
"""

import json
from collections import defaultdict
from nodes import Node
from utils.call_llm import call_llm


class OrderChaptersNode(Node):
    """Node for determining the logical order of chapters in the tutorial."""
    
    def process(self, context):
        """Determine the logical order of chapters in the tutorial.
        
        Args:
            context (dict): The shared context dictionary containing:
                - abstractions: List of abstraction dictionaries
                - relationships: List of relationship dictionaries
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                
        Returns:
            None: The context is updated directly with the chapter order.
        """
        abstractions = context["abstractions"]
        relationships = context["relationships"]
        verbose = context.get("verbose", False)
        
        if verbose:
            print("Determining logical order of chapters")
        
        # Try to determine the order using topological sort
        try:
            chapter_order = self._topological_sort(abstractions, relationships)
            if verbose:
                print("Determined chapter order using topological sort")
        except Exception as e:
            if verbose:
                print(f"Topological sort failed: {str(e)}")
                print("Falling back to LLM for chapter ordering")
            
            # Fall back to using the LLM for ordering
            chapter_order = self._llm_order(abstractions, relationships, context)
        
        # Create chapter metadata
        chapters = []
        for i, abstraction_name in enumerate(chapter_order):
            # Find the abstraction with this name
            abstraction = next((a for a in abstractions if a["name"] == abstraction_name), None)
            if abstraction:
                chapter_num = i + 1
                chapter = {
                    "number": chapter_num,
                    "title": f"Chapter {chapter_num}: {abstraction['name']}",
                    "abstraction": abstraction,
                    "filename": f"chapter_{chapter_num}_{abstraction['name'].lower().replace(' ', '_')}.md"
                }
                chapters.append(chapter)
        
        if verbose:
            print(f"Ordered {len(chapters)} chapters:")
            for chapter in chapters:
                print(f"  {chapter['number']}. {chapter['title']}")
        
        # Update the context with the chapter order
        context["chapters"] = chapters
        
        # Return None as we've updated the context directly
        return None
    
    def _topological_sort(self, abstractions, relationships):
        """Determine chapter order using topological sort.
        
        Args:
            abstractions (list): List of abstraction dictionaries
            relationships (list): List of relationship dictionaries
            
        Returns:
            list: Ordered list of abstraction names
        """
        # Create a graph of dependencies
        graph = defaultdict(list)
        in_degree = {a["name"]: 0 for a in abstractions}
        
        # Add edges to the graph
        for rel in relationships:
            source = rel["source"]
            target = rel["target"]
            
            # Skip self-references
            if source == target:
                continue
            
            graph[source].append(target)
            in_degree[target] = in_degree.get(target, 0) + 1
        
        # Find nodes with no dependencies
        queue = [a["name"] for a in abstractions if in_degree[a["name"]] == 0]
        
        # Perform topological sort
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if we visited all nodes
        if len(result) != len(abstractions):
            # There's a cycle in the graph, so we can't use topological sort
            # Fall back to a simple ordering based on abstraction type
            result = [a["name"] for a in sorted(abstractions, key=lambda a: (
                # Order by abstraction type (interfaces first, then classes, etc.)
                0 if a["type"] == "interface" else
                1 if a["type"] == "class" else
                2 if a["type"] == "module" else
                3
            ))]
        
        return result
    
    def _llm_order(self, abstractions, relationships, context):
        """Determine chapter order using an LLM.
        
        Args:
            abstractions (list): List of abstraction dictionaries
            relationships (list): List of relationship dictionaries
            context (dict): The shared context dictionary
            
        Returns:
            list: Ordered list of abstraction names
        """
        # Create the LLM prompt
        prompt = """
        You are an expert code educator. Your task is to determine the most logical order for explaining the key abstractions in a codebase.
        
        The order should follow these principles:
        1. Start with foundational components that others depend on
        2. Explain prerequisites before their dependents
        3. Group related abstractions together
        4. Consider the learning curve (simpler concepts first)
        
        Format your response as a JSON array of abstraction names in the order they should be explained:
        ["AbstractionName1", "AbstractionName2", ...]
        
        Here are the abstractions that have been identified:
        
        """
        
        # Add abstractions to the prompt
        prompt += json.dumps(abstractions, indent=2)
        
        # Add relationships to the prompt
        prompt += "\n\nHere are the relationships between abstractions:\n\n"
        prompt += json.dumps(relationships, indent=2)
        
        # Call the LLM to determine the order
        llm_response = call_llm(
            prompt=prompt,
            provider=context.get("llm_provider", "openai"),
            api_key=context.get("api_key"),
            max_tokens=1000,
            temperature=0.2
        )
        
        # Parse the LLM response to extract the order
        json_start = llm_response.find("[")
        json_end = llm_response.rfind("]") + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("Failed to extract JSON from LLM response")
        
        json_str = llm_response[json_start:json_end]
        
        try:
            order = json.loads(json_str)
            return order
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
