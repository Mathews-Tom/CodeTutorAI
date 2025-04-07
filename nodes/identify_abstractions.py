"""
EnlightenAI - Identify Abstractions Node

This module contains the IdentifyAbstractionsNode class, which is responsible for
identifying key abstractions (components, classes, modules) in the codebase.
"""

import json

from nodes import Node
from utils.call_llm import call_llm


class IdentifyAbstractionsNode(Node):
    """Node for identifying key abstractions in the codebase."""

    def process(self, context):
        """Identify key abstractions in the codebase.

        Args:
            context (dict): The shared context dictionary containing:
                - files: Dictionary mapping file paths to file contents
                - web_content: Dictionary containing web crawl results
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the identified abstractions.
        """
        files = context["files"]
        web_content = context.get("web_content", {})
        verbose = context.get("verbose", False)

        if verbose:
            print(f"Identifying abstractions from {len(files)} files")
            if web_content:
                print(f"Including web content in analysis")

        # Prepare file summaries for the LLM prompt
        file_summaries = []
        for path, content in files.items():
            # Limit content length to avoid token limits
            if len(content) > 5000:
                content = content[:5000] + "... [truncated]"

            file_summaries.append({"path": path, "content": content})

        # Add web content if available
        web_markdown = web_content.get("fit_markdown") or web_content.get(
            "markdown", ""
        )
        if web_markdown:
            # Limit web content length to avoid token limits
            if len(web_markdown) > 10000:
                web_markdown = web_markdown[:10000] + "... [truncated]"

            file_summaries.append({"path": "web_content.md", "content": web_markdown})

        # Create the LLM prompt
        prompt = self._create_abstraction_prompt(file_summaries)

        # Call the LLM to identify abstractions
        llm_response = call_llm(
            prompt=prompt,
            provider=context.get("llm_provider", "openai"),
            api_key=context.get("api_key"),
            max_tokens=2000,
            temperature=0.2,
        )

        # Parse the LLM response to extract abstractions
        abstractions = self._parse_abstractions(llm_response)

        if verbose:
            print(f"Identified {len(abstractions)} abstractions")
            for abstraction in abstractions:
                abstraction_type = abstraction.get("type", "N/A")
                print(f"  - {abstraction['name']}: {abstraction_type}")

        # Update the context with the identified abstractions
        context["abstractions"] = abstractions

        # Return None as we've updated the context directly
        return None

    def _create_abstraction_prompt(self, file_summaries):
        """Create a prompt for the LLM to identify abstractions.

        Args:
            file_summaries (list): List of dictionaries containing file paths and contents

        Returns:
            str: The prompt for the LLM
        """
        prompt = """
        You are an expert code analyzer. Your task is to identify key abstractions (components, classes, modules) in the following codebase.

        For each abstraction, provide:
        1. A unique name
        2. The type of abstraction (e.g., class, module, function, interface)
        3. A brief description of its purpose
        4. The file(s) where it is defined or implemented
        5. Key responsibilities or features

        Format your response as a JSON array of objects with the following structure:
        [
            {
                "name": "AbstractionName",
                "type": "class|module|function|interface",
                "description": "Brief description of the abstraction",
                "files": ["path/to/file1.py", "path/to/file2.py"],
                "responsibilities": ["Responsibility 1", "Responsibility 2"]
            },
            ...
        ]

        Focus on the most important abstractions that would help someone understand the overall architecture of the codebase.
        Limit your response to the top 10-15 most significant abstractions.

        Here are the files in the codebase:

        """

        for file_summary in file_summaries:
            prompt += f"\n--- {file_summary['path']} ---\n"
            prompt += file_summary["content"]
            prompt += "\n\n"

        prompt += "\nJSON response:"

        return prompt

    def _parse_abstractions(self, llm_response):
        """Parse the LLM response to extract abstractions.

        Args:
            llm_response (str): The LLM response containing JSON data

        Returns:
            list: List of abstraction dictionaries
        """
        # Extract JSON from the response (the LLM might include explanatory text)
        json_start = llm_response.find("[")
        json_end = llm_response.rfind("]") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("Failed to extract JSON from LLM response")

        json_str = llm_response[json_start:json_end]

        try:
            abstractions = json.loads(json_str)
            return abstractions
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
