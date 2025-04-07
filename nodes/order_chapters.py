"""
EnlightenAI - Order Chapters Node

This module contains the OrderChaptersNode class, which is responsible for
determining the logical order of chapters in the tutorial.
"""

import json
import re
from collections import defaultdict

from tqdm import tqdm

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
                - relationship_graph: Dictionary representing the relationship graph
                - ordering_method: Method to use for ordering ("auto", "topological", "learning_curve", "llm")
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the chapter order.
        """
        abstractions = context["abstractions"]
        relationships = context["relationships"]
        relationship_graph = context.get("relationship_graph", {})
        ordering_method = context.get("ordering_method", "auto")
        verbose = context.get("verbose", False)

        if verbose:
            print("Determining logical order of chapters")

        # Skip if no abstractions were identified
        if not abstractions:
            if verbose:
                print("No abstractions to order. Skipping chapter ordering.")
            context["chapters"] = []
            return None

        # Determine the ordering method to use
        if ordering_method == "auto":
            # Try different methods in order of preference
            methods = ["topological", "learning_curve", "llm"]
        else:
            # Use the specified method
            methods = [ordering_method]

        chapter_order = None
        used_method = None

        with tqdm(
            total=len(methods), desc="Trying ordering methods", disable=not verbose
        ) as pbar:
            for method in methods:
                try:
                    if method == "topological":
                        chapter_order = self._topological_sort(
                            abstractions, relationships
                        )
                        used_method = "topological sort"
                    elif method == "learning_curve":
                        chapter_order = self._learning_curve_sort(
                            abstractions, relationships, relationship_graph
                        )
                        used_method = "learning curve analysis"
                    elif method == "llm":
                        chapter_order = self._llm_order(
                            abstractions, relationships, context
                        )
                        used_method = "LLM suggestion"

                    # If we got a valid order, break the loop
                    if chapter_order and len(chapter_order) == len(abstractions):
                        break
                except Exception as e:
                    if verbose:
                        pbar.write(f"{method} ordering failed: {str(e)}")

                pbar.update(1)

        # If all methods failed, use a simple alphabetical order
        if not chapter_order or len(chapter_order) != len(abstractions):
            chapter_order = [
                a["name"] for a in sorted(abstractions, key=lambda a: a["name"])
            ]
            used_method = "alphabetical order"

        if verbose:
            print(f"Determined chapter order using {used_method}")

        # Create chapter metadata
        chapters = []
        for i, abstraction_name in enumerate(chapter_order):
            # Find the abstraction with this name
            abstraction = next(
                (a for a in abstractions if a["name"] == abstraction_name), None
            )
            if abstraction:
                chapter_num = i + 1

                # Create a clean filename
                clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", abstraction["name"].lower())
                filename = f"chapter_{chapter_num}_{clean_name}.md"

                chapter = {
                    "number": chapter_num,
                    "title": f"Chapter {chapter_num}: {abstraction['name']}",
                    "abstraction": abstraction,
                    "filename": filename,
                }
                chapters.append(chapter)

        if verbose:
            print(f"Ordered {len(chapters)} chapters:")
            for chapter in chapters:
                print(f"  {chapter['number']}. {chapter['title']}")

        # Update the context with the chapter order
        context["chapters"] = chapters
        context["ordering_method_used"] = used_method

        # Return None as we've updated the context directly
        return None

    def _learning_curve_sort(self, abstractions, _relationships, relationship_graph):
        """Determine chapter order based on learning curve complexity.

        Args:
            abstractions (list): List of abstraction dictionaries
            _relationships (list): List of relationship dictionaries (unused)
            relationship_graph (dict): Dictionary representing the relationship graph

        Returns:
            list: Ordered list of abstraction names
        """
        # Calculate complexity scores for each abstraction
        complexity_scores = {}

        for abstraction in abstractions:
            name = abstraction["name"]

            # Base score from abstraction type (interfaces and simple functions are easier)
            if abstraction.get("type") == "interface":
                base_score = 1
            elif abstraction.get("type") == "function":
                base_score = 2
            elif abstraction.get("type") == "class":
                base_score = 3
            else:
                base_score = 2

            # Add complexity based on number of responsibilities
            responsibility_score = len(abstraction.get("responsibilities", [])) * 0.5

            # Add complexity based on number of dependencies
            dependency_score = 0
            if name in relationship_graph:
                dependency_score = len(relationship_graph[name]) * 0.5

            # Add complexity based on number of dependents
            dependent_score = 0
            for source, targets in relationship_graph.items():
                if source != name:  # Skip self-references
                    for target in targets:
                        if target["target"] == name:
                            dependent_score += 0.5

            # Calculate total complexity score
            total_score = (
                base_score + responsibility_score + dependency_score + dependent_score
            )
            complexity_scores[name] = total_score

        # Sort abstractions by complexity score (ascending)
        sorted_abstractions = sorted(
            abstractions, key=lambda a: complexity_scores[a["name"]]
        )

        # Extract names in order
        return [a["name"] for a in sorted_abstractions]

    def _topological_sort(self, abstractions, relationships):
        """Determine chapter order using topological sort with cycle detection.

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
            rel_type = rel.get("type", "")

            # Skip self-references
            if source == target:
                continue

            # Skip certain relationship types for topological sorting
            # (e.g., "uses" relationships don't necessarily imply a dependency order)
            if rel_type in ["calls", "uses"]:
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
            # There's a cycle in the graph
            # Try to break cycles by removing edges with lowest priority
            remaining = set(a["name"] for a in abstractions) - set(result)

            # Find a node in the cycle with the lowest in-degree
            while remaining:
                # Find node with minimum in-degree among remaining nodes
                min_node = min(remaining, key=lambda n: in_degree.get(n, 0))

                # Add it to the result
                result.append(min_node)
                remaining.remove(min_node)

                # Update in-degrees for its neighbors
                for neighbor in graph[min_node]:
                    if neighbor in remaining:
                        in_degree[neighbor] -= 1

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

        IMPORTANT: Your response MUST include ALL abstraction names exactly as they appear in the input, and ONLY those names.

        Here are the abstractions that have been identified:

        """

        # Add abstractions to the prompt
        prompt += json.dumps(abstractions, indent=2)

        # Add relationships to the prompt
        prompt += "\n\nHere are the relationships between abstractions:\n\n"
        prompt += json.dumps(relationships, indent=2)

        # Add relationship types explanation
        prompt += """

        Relationship types and their meanings:
        - inherits: Inheritance relationship (e.g., class extends another class)
        - implements: Implementation relationship (e.g., class implements an interface)
        - composes: Composition relationship (e.g., class has an instance of another class)
        - aggregates: Aggregation relationship (e.g., class has a collection of another class)
        - uses: Usage relationship (e.g., class calls methods of another class)
        - depends: Dependency relationship (e.g., class depends on another class)
        - creates: Creation relationship (e.g., class creates instances of another class)
        - calls: Method call relationship (e.g., method calls another method)
        - imports: Import relationship (e.g., file imports another file)
        """

        # Call the LLM to determine the order
        llm_response = call_llm(
            prompt=prompt,
            provider=context.get("llm_provider", "openai"),
            api_key=context.get("api_key"),
            max_tokens=1000,
            temperature=0.2,
        )

        # Parse the LLM response to extract the order
        json_start = llm_response.find("[")
        json_end = llm_response.rfind("]") + 1

        if json_start == -1 or json_end == 0:
            # Try to find JSON in a code block
            code_block_pattern = r"```(?:json)?\s*\n(.+?)\n```"
            code_block_match = re.search(code_block_pattern, llm_response, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1).strip()
            else:
                raise ValueError("Failed to extract JSON from LLM response")
        else:
            json_str = llm_response[json_start:json_end]

        try:
            order = json.loads(json_str)

            # Validate that all abstractions are included
            abstraction_names = {a["name"] for a in abstractions}
            order_set = set(order)

            # Check for missing abstractions
            missing = abstraction_names - order_set
            if missing:
                # Add missing abstractions to the end
                order.extend(list(missing))

            # Check for extra abstractions
            extra = order_set - abstraction_names
            if extra:
                # Remove extra abstractions
                order = [name for name in order if name in abstraction_names]

            return order
        except json.JSONDecodeError:
            # Try to fix common JSON errors
            fixed_json_str = self._fix_json_errors(json_str)
            try:
                order = json.loads(fixed_json_str)
                return order
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")

    def _fix_json_errors(self, json_str):
        """Fix common JSON errors in LLM responses.

        Args:
            json_str (str): JSON string with potential errors

        Returns:
            str: Fixed JSON string
        """
        # Replace single quotes with double quotes
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)

        # Fix trailing commas in arrays
        json_str = re.sub(r",\s*]", r"]", json_str)

        # Fix missing quotes around keys
        json_str = re.sub(r"([{,])\s*([a-zA-Z0-9_]+)\s*:", r'\1"\2":', json_str)

        return json_str
