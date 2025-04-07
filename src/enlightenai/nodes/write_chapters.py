"""
EnlightenAI - Write Chapters Node

This module contains the WriteChaptersNode class for generating tutorial chapters.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any, Dict, List, Optional

from tqdm import tqdm

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

        if verbose:
            print(f"Generating {len(ordered_chapters)} chapters...")
            print(f"Tutorial depth: {depth}")
            print(f"Tutorial language: {language}")
            print(f"Generate diagrams: {generate_diagrams}")

        # Create the chapters directory
        chapters_dir = os.path.join(output_dir, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)

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

        # Get the progress manager
        progress_manager = context.get("progress_manager")

        # Update node progress
        if progress_manager:
            progress_manager.update_node_progress(20)

        # Generate chapters in parallel
        chapters = []

        def generate_chapter(chapter_index):
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
                }

            # Get related abstractions
            related_abstractions = []
            if abstraction["name"] in relationships:
                related_abstractions = relationships[abstraction["name"]]

            # Create the prompt
            prompt = self._create_chapter_prompt(
                abstraction,
                related_abstractions,
                chapter_number,
                len(ordered_chapters),
                depth,
                language,
                generate_diagrams,
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

            # Save the chapter
            chapter_filename = f"chapter_{chapter_number:02d}_{self._sanitize_filename(chapter_title)}.md"
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
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Create a progress bar for chapters
            chapters_pbar = None
            if progress_manager:
                # Make sure we have at least one chapter to process
                if ordered_chapters:
                    chapters_pbar = progress_manager.get_task_pbar(
                        "Chapters",
                        len(ordered_chapters),
                        desc="    Generating chapters",
                        unit="chapter",
                    )
            elif verbose and ordered_chapters:
                chapters_pbar = tqdm(
                    total=len(ordered_chapters),
                    desc="Generating chapters",
                    unit="chapter",
                )

            # Update node progress
            if progress_manager:
                progress_manager.update_node_progress(30)

            # Only submit tasks if we have chapters to process
            if ordered_chapters:
                # Submit all tasks
                future_to_index = {
                    executor.submit(generate_chapter, i): i
                    for i in range(len(ordered_chapters))
                }

                # Process results as they complete
                for future in future_to_index:
                    chapter = future.result()
                    chapters.append(chapter)
                    if chapters_pbar:
                        chapters_pbar.update(1)

            # Close the progress bar if we created it
            if progress_manager:
                progress_manager.close_task_pbar("Chapters")
            elif chapters_pbar:
                chapters_pbar.close()

        # Sort chapters by number
        chapters.sort(key=lambda x: x["number"])

        # Update node progress
        if progress_manager:
            progress_manager.update_node_progress(90)

        # Update the context
        context["chapters"] = chapters

        if verbose:
            print(f"Generated {len(chapters)} chapters")

        # Complete node progress
        if progress_manager:
            progress_manager.update_node_progress(100)

        return None

    def _create_chapter_prompt(
        self,
        abstraction: Dict[str, Any],
        related_abstractions: List[str],
        chapter_number: int,
        total_chapters: int,
        depth: str,
        language: str,
        generate_diagrams: bool,
        diagrams: Dict[str, str],
    ) -> str:
        """Create a prompt for generating a chapter.

        Args:
            abstraction (dict): The abstraction for this chapter
            related_abstractions (list): List of related abstractions
            chapter_number (int): The chapter number
            total_chapters (int): The total number of chapters
            depth (str): Depth of the tutorial (basic, intermediate, advanced)
            language (str): Language for the tutorial
            generate_diagrams (bool): Whether to generate diagrams
            diagrams (dict): Dictionary of generated diagrams

        Returns:
            str: The prompt for generating the chapter
        """
        # Determine previous and next chapters
        prev_chapter = f"Chapter {chapter_number - 1}" if chapter_number > 1 else "None"
        next_chapter = (
            f"Chapter {chapter_number + 1}"
            if chapter_number < total_chapters
            else "None"
        )

        # Create the prompt
        prompt = f"""
You are an expert software developer and technical writer. Your task is to write Chapter {chapter_number} of a tutorial about a codebase.

# Chapter Information
- Title: {abstraction["name"]}
- Description: {abstraction["description"]}
- Previous Chapter: {prev_chapter}
- Next Chapter: {next_chapter}
- Tutorial Depth: {depth}
- Language: {language}

# Key Files
{json.dumps(abstraction["files"], indent=2)}

# Related Components
{", ".join(related_abstractions)}

# Instructions
Write a comprehensive tutorial chapter about {abstraction["name"]}. The chapter should:
1. Start with a clear introduction to the component
2. Explain its purpose and role in the overall system
3. Describe how it works and interacts with other components
4. Include code examples and explanations
5. End with a summary and transition to the next chapter

"""

        # Add depth-specific instructions
        if depth == "basic":
            prompt += """
# Depth: Basic
- Focus on high-level concepts and simple explanations
- Avoid complex technical details
- Use analogies and simple examples
- Assume the reader has minimal programming experience
"""
        elif depth == "intermediate":
            prompt += """
# Depth: Intermediate
- Balance conceptual explanations with technical details
- Include relevant code examples with explanations
- Discuss design patterns and architectural decisions
- Assume the reader has moderate programming experience
"""
        elif depth == "advanced":
            prompt += """
# Depth: Advanced
- Provide in-depth technical explanations
- Include detailed code examples and edge cases
- Discuss performance considerations and optimizations
- Analyze design decisions and trade-offs
- Assume the reader has significant programming experience
"""

        # Add diagram information if available
        if generate_diagrams and diagrams:
            prompt += """
# Diagrams
Include references to the following diagrams where appropriate:
"""
            for diagram_type, diagram_content in diagrams.items():
                prompt += f"- {diagram_type.replace('_', ' ').title()}\n"

        # Format the output
        prompt += """
# Output Format
Format your response as a Markdown document with the following structure:
- Title (H1): "Chapter X: Component Name"
- Introduction
- Main sections with appropriate headings (H2, H3)
- Code examples in Markdown code blocks
- Summary
- "Next Chapter" and "Previous Chapter" links at the end

Do not include any explanatory text outside the chapter content.
"""

        return prompt

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename by replacing invalid characters.

        Args:
            filename (str): The filename to sanitize

        Returns:
            str: The sanitized filename
        """
        # Replace spaces with underscores
        filename = filename.replace(" ", "_")

        # Remove invalid characters
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "")

        return filename.lower()
