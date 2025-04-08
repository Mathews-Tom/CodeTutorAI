"""
EnlightenAI - Write Chapters Node

This module contains the WriteChaptersNode class for generating tutorial chapters.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from tqdm import tqdm

from enlightenai.nodes.node import Node
from enlightenai.utils.diagram_generator import generate_diagrams
from enlightenai.utils.llm_client import LLMClient  # Import the client class


class WriteChaptersNode(Node):
    """Node for generating tutorial chapters."""

    def process(self, context):
        """Generate tutorial chapters based on the ordered abstractions.

        Args:
            context (dict): The shared context dictionary containing:
                - abstractions: List of abstractions
                - relationships: Dictionary of relationships between abstractions
                - ordered_chapters: List of ordered chapter titles
                - file_paths: List of relative file paths in the repository (optional, used for diagrams)
                - repo_dir: Local path to the cloned repository
                - output_dir: Output directory for the tutorial
                - batch_size: Number of chapters to generate in parallel
                - llm_provider: LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                - depth: Depth of the tutorial (basic, intermediate, advanced)
                - language: Language for the tutorial
                - generate_diagrams: Whether to generate diagrams
                - cache_enabled: Whether to enable LLM caching
                - cache_dir: Directory for the LLM cache

        Returns:
            None: The context is updated directly with the generated chapters.
        """
        verbose = context.get("verbose", False)
        output_dir = context.get("output_dir", "tutorial_output")
        batch_size = context.get("batch_size", 1)
        llm_provider = context.get("llm_provider", "openai")
        api_key = context.get("api_key")
        depth = context.get("depth", "intermediate")
        language = context.get("language", "en")
        should_generate_diagrams = context.get(
            "generate_diagrams", False
        )  # Renamed to avoid shadowing imported function
        cache_enabled = context.get("cache_enabled", False)
        cache_dir = context.get("cache_dir", ".llm_cache")
        repo_dir = context.get("repo_dir")  # Needed for reading files

        # Get the ordered chapters
        ordered_chapters = context.get("ordered_chapters", [])
        abstractions = context.get("abstractions", [])
        relationships = context.get("relationships", {})
        # files = context.get("files", {}) # No longer used directly

        if not repo_dir:
            raise ValueError("repo_dir is required in the context to read files.")

        # Create the chapters directory
        chapters_dir = os.path.join(output_dir, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)

        # Check if we have any chapters to generate
        if not ordered_chapters:
            if verbose:
                print("No chapters to generate. Skipping chapter generation.")

            # Update the context with an empty chapters list
            context["chapters"] = []
            return None  # Exit early if no chapters

        if verbose:
            print(f"Generating {len(ordered_chapters)} chapters...")
            print(f"Tutorial depth: {depth}")
            print(f"Tutorial language: {language}")
            print(f"Generate diagrams: {should_generate_diagrams}")

        # Generate diagrams if requested
        diagrams = {}
        if should_generate_diagrams:
            if verbose:
                print("Generating diagrams...")
            # Call the imported function, not the boolean flag
            diagrams = generate_diagrams(
                repo_dir, abstractions, verbose=verbose
            )  # Use the imported function

            # Save diagrams to files
            diagrams_dir = os.path.join(output_dir, "diagrams")
            os.makedirs(diagrams_dir, exist_ok=True)

            for diagram_type, diagram_content in diagrams.items():
                diagram_path = os.path.join(diagrams_dir, f"{diagram_type}.md")
                with open(diagram_path, "w", encoding="utf-8") as f:
                    f.write(diagram_content)

            if verbose:
                print(f"Saved diagrams to {diagrams_dir}")
        # Instantiate the LLM client with caching settings
        llm_client = LLMClient(
            provider=llm_provider,
            api_key=api_key,
            cache_enabled=cache_enabled,
            cache_dir=cache_dir,
            verbose=verbose,  # Pass verbose setting to client for cache logging
        )

        # Generate chapters in parallel
        chapters = []

        def generate_chapter(chapter_index):
            """Generate a single chapter (defined inside process)."""
            # Note: This function uses variables from the outer scope (process method)
            # like llm_client, abstractions, relationships, repo_dir, etc.

            chapter_title = ordered_chapters[chapter_index]
            chapter_number = chapter_index + 1

            # Find the abstraction for this chapter
            abstraction = None
            for a in abstractions:
                if a["name"] == chapter_title:
                    abstraction = a
                    break

            if not abstraction:
                if verbose:
                    print(f"Warning: No abstraction found for chapter {chapter_title}")
                return {
                    "title": chapter_title,
                    "content": f"# Chapter {chapter_number}: {chapter_title}\n\nNo content available for this chapter.",
                    "number": chapter_number,
                    "filename": f"chapter_{chapter_number:02d}.md",
                }

            # Get the abstraction details
            abstraction_name = abstraction["name"]
            abstraction_description = abstraction.get("description", "")
            abstraction_files = abstraction.get("files", [])

            # Get the related abstractions
            related_abstractions = relationships.get(abstraction_name, [])

            # Create the prompt for the LLM
            # Note: _create_chapter_prompt is a method of the class, so use self.
            prompt = self._create_chapter_prompt(
                abstraction,
                related_abstractions,
                repo_dir,  # Pass repo_dir
                chapter_number,
                depth,
                language,
                diagrams,
            )

            # Call the LLM
            chapter_content = (
                llm_client.call(  # Use the client instance from outer scope
                    prompt,
                    # provider and api_key are handled by the client instance
                    max_tokens=4000,
                    temperature=0.7,
                )
            )

            # Format the chapter content
            # Note: _format_chapter_content is a method of the class, so use self.
            chapter_content = self._format_chapter_content(
                chapter_content, chapter_number, chapter_title
            )

            # Create the chapter filename
            chapter_filename = f"chapter_{chapter_number:02d}.md"

            # Save the chapter to a file
            chapter_path = os.path.join(chapters_dir, chapter_filename)
            with open(chapter_path, "w", encoding="utf-8") as f:
                f.write(chapter_content)

            # Print completion message if verbose
            if verbose:
                print(f"Generated chapter {chapter_number}: {chapter_title}")

            return {
                "title": chapter_title,
                "content": chapter_content,
                "number": chapter_number,
                "filename": chapter_filename,
            }

        # Use ThreadPoolExecutor to generate chapters in parallel
        if verbose:
            print(f"Generating {len(ordered_chapters)} chapters in parallel...")

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit all tasks
            futures = []
            for i in range(len(ordered_chapters)):
                future = executor.submit(generate_chapter, i)
                futures.append(future)

            # Process results as they complete
            with tqdm(
                total=len(futures),
                desc="Generating chapters",
                unit="chapter",
                disable=not verbose,
            ) as pbar:
                for future in futures:
                    chapter = future.result()
                    chapters.append(chapter)
                    pbar.update(1)

        # Sort chapters by number
        chapters.sort(key=lambda x: x["number"])

        # Update the context
        context["chapters"] = chapters

        if verbose:
            print(f"Generated {len(chapters)} chapters")

        # No return value needed as context is updated directly
        return None

    def _create_chapter_prompt(
        self,
        abstraction: Dict[str, Any],
        related_abstractions: List[str],
        repo_dir: str,  # Changed from files dict
        chapter_number: int,
        depth: str,
        language: str,
        diagrams: Dict[str, str],
    ) -> str:
        """Create a prompt for the LLM to generate a chapter.

        Args:
            abstraction (dict): The abstraction to generate a chapter for
            related_abstractions (list): List of related abstraction names
            repo_dir (str): Local path to the cloned repository
            chapter_number (int): The chapter number
            depth (str): The depth of the tutorial (basic, intermediate, advanced)
            language (str): The language for the tutorial
            diagrams (dict): Dictionary of generated diagrams

        Returns:
            str: The prompt for the LLM
        """
        # Get the abstraction details
        abstraction_name = abstraction["name"]
        abstraction_description = abstraction.get("description", "")
        abstraction_files = abstraction.get("files", [])

        # Create the prompt
        prompt = f"""
You are an expert software developer and technical writer. Your task is to write Chapter {chapter_number} of a tutorial about the {abstraction_name} component.

# Chapter Information
- Title: {abstraction_name}
- Description: {abstraction_description}
- Files: {", ".join(abstraction_files)}
- Related Components: {", ".join(related_abstractions)}

# Tutorial Depth
The tutorial should be at a {depth} level:
"""

        # Add depth-specific instructions
        if depth == "basic":
            prompt += """
- Focus on high-level concepts and simple explanations
- Avoid complex technical details
- Use simple code examples
- Explain concepts in a way that beginners can understand
"""
        elif depth == "advanced":
            prompt += """
- Include in-depth technical details
- Explain complex interactions and edge cases
- Use detailed code examples
- Assume the reader has a strong technical background
"""
        else:  # intermediate (default)
            prompt += """
- Balance conceptual explanations with technical details
- Include relevant code examples
- Explain important interactions with other components
- Assume the reader has some programming experience
"""

        # Add language-specific instructions
        if language != "en":
            prompt += f"""
# Language
Write the tutorial in {language} language. Ensure that technical terms are correctly translated or kept in English if that's the convention in {language}.
"""

        # Add file content
        prompt += """
# Files
Here are the contents of the relevant files:
"""

        for file_path in abstraction_files:
            full_path = os.path.join(repo_dir, file_path)
            file_content = (
                f"Content for {file_path} could not be read."  # Default message
            )
            try:
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        # Read content and truncate
                        file_content = f.read()[:2000]
                else:
                    file_content = f"File {file_path} not found."
            except Exception as e:
                file_content = f"Error reading {file_path}: {e}"

            prompt += f"""
## {file_path}
```
{file_content}
```
"""

        # Add related abstractions
        if related_abstractions:
            prompt += """
# Related Components
This component interacts with the following components:
"""

            for related in related_abstractions:
                prompt += f"- {related}\n"

        # Add diagrams
        if diagrams:
            prompt += """
# Diagrams
Include references to the following diagrams where appropriate:
"""
            for diagram_type, diagram_content in diagrams.items():
                prompt += f"- {diagram_type.replace('_', ' ').title()}\n"

        # Format the output
        prompt += """
# Output Format
Write a comprehensive tutorial chapter in Markdown format. Include:
1. A clear heading with the chapter number and title
2. An introduction explaining the purpose and importance of this component
3. Detailed explanations of how the component works
4. Code examples with explanations
5. Interactions with other components
6. Best practices and common patterns
7. A summary of key points

Make the tutorial engaging, clear, and informative. Use proper Markdown formatting for headings, code blocks, lists, etc.
"""

        return prompt

    def _format_chapter_content(
        self, content: str, chapter_number: int, chapter_title: str
    ) -> str:
        """Format the chapter content.

        Args:
            content (str): The raw chapter content
            chapter_number (int): The chapter number
            chapter_title (str): The chapter title

        Returns:
            str: The formatted chapter content
        """
        # Ensure the chapter starts with a proper heading
        if not content.strip().startswith(f"# Chapter {chapter_number}"):
            content = f"# Chapter {chapter_number}: {chapter_title}\n\n{content}"

        # Add attribution to the end of the chapter
        attribution = "\n\n---\n\n*This tutorial was generated by [🪄EnlightenAI🔍](https://github.com/Mathews-Tom/EnlightenAI), an intelligent codebase explainer.*"
        content += attribution

        return content
