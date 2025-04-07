"""
EnlightenAI - Write Chapters Node

This module contains the WriteChaptersNode class for generating tutorial chapters.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from enlightenai.nodes.node import Node
from enlightenai.utils.call_llm import call_llm
from enlightenai.utils.diagram_generator import generate_diagrams


class WriteChaptersNode(Node):
    """Node for generating tutorial chapters."""

    def process(self, context):
        """Generate tutorial chapters based on the ordered abstractions.

        Args:
            context (dict): The shared context dictionary containing:
                - abstractions: List of abstractions
                - relationships: Dictionary of relationships between abstractions
                - ordered_chapters: List of ordered chapter titles
                - files: Dictionary of file contents
                - output_dir: Output directory for the tutorial
                - batch_size: Number of chapters to generate in parallel
                - llm_provider: LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                - depth: Depth of the tutorial (basic, intermediate, advanced)
                - language: Language for the tutorial
                - generate_diagrams: Whether to generate diagrams

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
        generate_diagrams = context.get("generate_diagrams", False)

        # Get the ordered chapters
        ordered_chapters = context.get("ordered_chapters", [])
        abstractions = context.get("abstractions", [])
        relationships = context.get("relationships", {})
        files = context.get("files", {})

        # Create the chapters directory
        chapters_dir = os.path.join(output_dir, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)

        # Check if we have any chapters to generate
        if not ordered_chapters:
            if verbose:
                print("No chapters to generate. Skipping chapter generation.")

            # Update the context with an empty chapters list
            context["chapters"] = []
            return None

        if verbose:
            print(f"Generating {len(ordered_chapters)} chapters...")
            print(f"Tutorial depth: {depth}")
            print(f"Tutorial language: {language}")
            print(f"Generate diagrams: {generate_diagrams}")

        # Generate diagrams if requested
        diagrams = {}
        if generate_diagrams:
            if verbose:
                print("Generating diagrams...")
            diagrams = generate_diagrams(files)

            # Save diagrams to files
            diagrams_dir = os.path.join(output_dir, "diagrams")
            os.makedirs(diagrams_dir, exist_ok=True)

            for diagram_type, diagram_content in diagrams.items():
                diagram_path = os.path.join(diagrams_dir, f"{diagram_type}.md")
                with open(diagram_path, "w", encoding="utf-8") as f:
                    f.write(diagram_content)

            if verbose:
                print(f"Saved diagrams to {diagrams_dir}")

        # Generate chapters in parallel
        chapters = []

        def generate_chapter(chapter_index):
            """Generate a single chapter.

            Args:
                chapter_index (int): Index of the chapter in the ordered_chapters list

            Returns:
                dict: The generated chapter
            """
            start_time = time.time()
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
            prompt = self._create_chapter_prompt(
                abstraction,
                related_abstractions,
                files,
                chapter_number,
                depth,
                language,
                diagrams,
            )

            # Call the LLM
            chapter_content = call_llm(
                prompt,
                provider=llm_provider,
                api_key=api_key,
                max_tokens=4000,
                temperature=0.7,
            )

            # Format the chapter content
            chapter_content = self._format_chapter_content(
                chapter_content, chapter_number, chapter_title
            )

            # Create the chapter filename
            chapter_filename = f"chapter_{chapter_number:02d}.md"

            # Save the chapter to a file
            chapter_path = os.path.join(chapters_dir, chapter_filename)
            with open(chapter_path, "w", encoding="utf-8") as f:
                f.write(chapter_content)

            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

            # Print completion message
            print(f"Generated chapter {chapter_number}: {chapter_title} in {time_str}")

            return {
                "title": chapter_title,
                "content": chapter_content,
                "number": chapter_number,
                "filename": chapter_filename,
                "elapsed_time": elapsed_time,
                "time_str": time_str,
            }

        # Use ThreadPoolExecutor to generate chapters in parallel
        print(f"Generating {len(ordered_chapters)} chapters in parallel...")

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit all tasks
            futures = []
            for i in range(len(ordered_chapters)):
                future = executor.submit(generate_chapter, i)
                futures.append(future)

            # Process results as they complete
            completed = 0
            total = len(futures)
            for future in futures:
                chapter = future.result()
                chapters.append(chapter)
                completed += 1
                print(f"Chapter generation progress: {completed}/{total}")

        # Sort chapters by number
        chapters.sort(key=lambda x: x["number"])

        # Update the context
        context["chapters"] = chapters

        if verbose:
            print(f"Generated {len(chapters)} chapters")

        return None

    def _create_chapter_prompt(
        self,
        abstraction: Dict[str, Any],
        related_abstractions: List[str],
        files: Dict[str, str],
        chapter_number: int,
        depth: str,
        language: str,
        diagrams: Dict[str, str],
    ) -> str:
        """Create a prompt for the LLM to generate a chapter.

        Args:
            abstraction (dict): The abstraction to generate a chapter for
            related_abstractions (list): List of related abstraction names
            files (dict): Dictionary of file contents
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
            if file_path in files:
                file_content = files[file_path]
                prompt += f"""
## {file_path}
```
{file_content[:2000]}  # Limit to 2000 characters to avoid token limits
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
