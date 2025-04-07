"""
EnlightenAI - Analyze Relationships Node

This module contains the AnalyzeRelationshipsNode class, which is responsible for
analyzing relationships between abstractions in the codebase.
"""

import json

from nodes import Node
from utils.call_llm import call_llm


class AnalyzeRelationshipsNode(Node):
    """Node for analyzing relationships between abstractions in the codebase."""

    def process(self, context):
        """Analyze relationships between abstractions in the codebase.

        Args:
            context (dict): The shared context dictionary containing:
                - files: Dictionary mapping file paths to file contents
                - web_content: Dictionary containing web crawl results
                - abstractions: List of abstraction dictionaries
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the identified relationships.
        """
        files = context["files"]
        web_content = context.get("web_content", {})
        abstractions = context["abstractions"]
        verbose = context.get("verbose", False)

        if verbose:
            print(f"Analyzing relationships between {len(abstractions)} abstractions")
            if web_content:
                print(f"Including web content in relationship analysis")

        # Add web content to files if available
        files_with_web = dict(files)
        web_markdown = web_content.get("fit_markdown") or web_content.get(
            "markdown", ""
        )
        if web_markdown:
            files_with_web["web_content.md"] = web_markdown

        # Create the LLM prompt
        prompt = self._create_relationship_prompt(abstractions, files_with_web)

        # Call the LLM to analyze relationships
        llm_response = call_llm(
            prompt=prompt,
            provider=context.get("llm_provider", "openai"),
            api_key=context.get("api_key"),
            max_tokens=2000,
            temperature=0.2,
        )

        # Parse the LLM response to extract relationships
        relationships = self._parse_relationships(llm_response)

        if verbose:
            print(f"Identified {len(relationships)} relationships")
            for relationship in relationships:
                print(
                    f"  - {relationship['source']} {relationship['type']} {relationship['target']}"
                )

        # Update the context with the identified relationships
        context["relationships"] = relationships

        # Return None as we've updated the context directly
        return None

    def _create_relationship_prompt(self, abstractions, files):
        """Create a prompt for the LLM to analyze relationships.

        Args:
            abstractions (list): List of abstraction dictionaries
            files (dict): Dictionary mapping file paths to file contents

        Returns:
            str: The prompt for the LLM
        """
        prompt = """
        You are an expert code analyzer. Your task is to identify relationships between the key abstractions in the codebase.

        For each relationship, provide:
        1. The source abstraction name
        2. The target abstraction name
        3. The type of relationship (e.g., inherits, uses, calls, imports)
        4. A brief description of the relationship

        Format your response as a JSON array of objects with the following structure:
        [
            {
                "source": "SourceAbstractionName",
                "target": "TargetAbstractionName",
                "type": "inherits|uses|calls|imports",
                "description": "Brief description of the relationship"
            },
            ...
        ]

        Here are the abstractions that have been identified:

        """

        # Add abstractions to the prompt
        prompt += json.dumps(abstractions, indent=2)

        # Add relevant file contents
        prompt += "\n\nHere are the relevant files:\n\n"

        # Get the files referenced by the abstractions
        relevant_files = set()
        for abstraction in abstractions:
            for file_path in abstraction.get("files", []):
                relevant_files.add(file_path)

        # Add the relevant file contents to the prompt
        for file_path in relevant_files:
            if file_path in files:
                content = files[file_path]
                # Limit content length to avoid token limits
                if len(content) > 3000:
                    content = content[:3000] + "... [truncated]"

                prompt += f"\n--- {file_path} ---\n"
                prompt += content
                prompt += "\n\n"

        prompt += "\nJSON response:"

        return prompt

    def _parse_relationships(self, llm_response):
        """Parse the LLM response to extract relationships.

        Args:
            llm_response (str): The LLM response containing JSON data

        Returns:
            list: List of relationship dictionaries
        """
        # Extract JSON from the response (the LLM might include explanatory text)
        json_start = llm_response.find("[")
        json_end = llm_response.rfind("]") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("Failed to extract JSON from LLM response")

        json_str = llm_response[json_start:json_end]

        try:
            relationships = json.loads(json_str)
            return relationships
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
