"""
EnlightenAI - Write Chapters Node

This module contains the WriteChaptersNode class, which is responsible for
generating Markdown content for each chapter in the tutorial.
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from nodes import Node
from utils.call_llm import call_llm
from utils.formatting import format_code_block, format_markdown


class WriteChaptersNode(Node):
    """Node for generating Markdown content for each chapter in the tutorial."""

    def process(self, context):
        """Generate Markdown content for each chapter in the tutorial.
        
        Args:
            context (dict): The shared context dictionary containing:
                - files: Dictionary mapping file paths to file contents
                - abstractions: List of abstraction dictionaries
                - relationships: List of relationship dictionaries
                - chapters: List of chapter dictionaries
                - output_dir: Output directory for the tutorial
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - batch_size: Number of chapters to generate in parallel (default: 1)
                - verbose: Whether to print verbose output
                
        Returns:
            None: The context is updated directly with the generated chapters.
        """
        files = context["files"]
        chapters = context["chapters"]
        relationships = context["relationships"]
        output_dir = context["output_dir"]
        batch_size = context.get("batch_size", 1)
        verbose = context.get("verbose", False)
        
        # Skip if no chapters were ordered
        if not chapters:
            if verbose:
                print("No chapters to generate. Skipping chapter generation.")
            return None
        
        # Create the chapters directory if it doesn't exist
        chapters_dir = os.path.join(output_dir, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)
        
        if verbose:
            print(f"Generating content for {len(chapters)} chapters")
        
        # Determine whether to use batch processing
        if batch_size > 1 and len(chapters) > 1:
            self._batch_generate_chapters(context, chapters_dir)
        else:
            self._sequential_generate_chapters(context, chapters_dir)
        
        # Return None as we've updated the context directly
        return None
        
    def _sequential_generate_chapters(self, context, chapters_dir):
        """Generate chapter content sequentially.
        
        Args:
            context (dict): The shared context dictionary
            chapters_dir (str): Directory to save chapter files
        """
        files = context["files"]
        chapters = context["chapters"]
        relationships = context["relationships"]
        verbose = context.get("verbose", False)
        
        # Generate content for each chapter sequentially
        with tqdm(total=len(chapters), desc="Generating chapters", disable=not verbose) as pbar:
            for chapter in chapters:
                if verbose:
                    pbar.write(f"Generating content for chapter {chapter['number']}: {chapter['title']}")
                
                # Get the abstraction for this chapter
                abstraction = chapter["abstraction"]
                
                # Find relationships involving this abstraction
                abstraction_relationships = [
                    rel for rel in relationships
                    if rel["source"] == abstraction["name"] or rel["target"] == abstraction["name"]
                ]
                
                # Create the LLM prompt
                prompt = self._create_chapter_prompt(abstraction, abstraction_relationships, files, chapters)
                
                # Call the LLM to generate the chapter content
                llm_response = call_llm(
                    prompt=prompt,
                    provider=context.get("llm_provider", "openai"),
                    api_key=context.get("api_key"),
                    max_tokens=3000,
                    temperature=0.5
                )
                
                # Post-process the content
                processed_content = self._post_process_content(llm_response, chapter, chapters)
                
                # Save the chapter content to a file
                chapter_path = os.path.join(chapters_dir, chapter["filename"])
                with open(chapter_path, "w") as f:
                    f.write(processed_content)
                
                # Add the content to the chapter dictionary
                chapter["content"] = processed_content
                
                if verbose:
                    pbar.write(f"Saved chapter to {chapter_path}")
                
                pbar.update(1)
    
    def _batch_generate_chapters(self, context, chapters_dir):
        """Generate chapter content in parallel batches.
        
        Args:
            context (dict): The shared context dictionary
            chapters_dir (str): Directory to save chapter files
        """
        files = context["files"]
        chapters = context["chapters"]
        relationships = context["relationships"]
        batch_size = context.get("batch_size", 1)
        verbose = context.get("verbose", False)
        
        # Function to generate a single chapter
        def generate_chapter(chapter):
            # Get the abstraction for this chapter
            abstraction = chapter["abstraction"]
            
            # Find relationships involving this abstraction
            abstraction_relationships = [
                rel for rel in relationships
                if rel["source"] == abstraction["name"] or rel["target"] == abstraction["name"]
            ]
            
            # Create the LLM prompt
            prompt = self._create_chapter_prompt(abstraction, abstraction_relationships, files, chapters)
            
            # Call the LLM to generate the chapter content
            llm_response = call_llm(
                prompt=prompt,
                provider=context.get("llm_provider", "openai"),
                api_key=context.get("api_key"),
                max_tokens=3000,
                temperature=0.5
            )
            
            # Post-process the content
            processed_content = self._post_process_content(llm_response, chapter, chapters)
            
            return chapter, processed_content
        
        # Generate content for chapters in parallel batches
        with tqdm(total=len(chapters), desc="Generating chapters", disable=not verbose) as pbar:
            # Process chapters in batches
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit all chapters for processing
                future_to_chapter = {executor.submit(generate_chapter, chapter): chapter for chapter in chapters}
                
                # Process completed chapters
                for future in as_completed(future_to_chapter):
                    chapter, content = future.result()
                    
                    # Save the chapter content to a file
                    chapter_path = os.path.join(chapters_dir, chapter["filename"])
                    with open(chapter_path, "w") as f:
                        f.write(content)
                    
                    # Add the content to the chapter dictionary
                    chapter["content"] = content
                    
                    if verbose:
                        pbar.write(f"Saved chapter {chapter['number']}: {chapter['title']} to {chapter_path}")
                    
                    pbar.update(1)
    
    def _post_process_content(self, content, chapter, chapters):
        """Post-process the generated content.
        
        Args:
            content (str): The raw content from the LLM
            chapter (dict): The chapter dictionary
            chapters (list): List of all chapter dictionaries
            
        Returns:
            str: The processed content
        """
        # Format the content
        processed_content = format_markdown(content)
        
        # Ensure the chapter has the correct title
        title = f"# Chapter {chapter['number']}: {chapter['abstraction']['name']}"
        if not processed_content.startswith("# Chapter"):
            processed_content = f"{title}\n\n{processed_content}"
        else:
            # Replace the existing title
            processed_content = re.sub(r"^# .*$", title, processed_content, flags=re.MULTILINE)
        
        # Add cross-references to other chapters
        other_chapters = [c for c in chapters if c["number"] != chapter["number"]]
        if other_chapters:
            references = "\n\n## Related Chapters\n\n"
            for c in other_chapters:
                if any(rel for rel in chapter.get("relationships", []) if rel["source"] == chapter["abstraction"]["name"] and rel["target"] == c["abstraction"]["name"] or rel["source"] == c["abstraction"]["name"] and rel["target"] == chapter["abstraction"]["name"]):
                    references += f"- [Chapter {c['number']}: {c['abstraction']['name']}](chapter_{c['number']}_{c['abstraction']['name'].lower().replace(' ', '_')}.md)\n"
            
            if references != "\n\n## Related Chapters\n\n":
                processed_content += references
        
        # Add a navigation footer
        processed_content += "\n\n---\n\n[Back to Index](../index.md)"
        
        return processed_content
    
    def _create_chapter_prompt(self, abstraction, relationships, files, chapters):
        """Create a prompt for the LLM to generate a chapter.
        
        Args:
            abstraction (dict): The abstraction for this chapter
            relationships (list): List of relationships involving this abstraction
            files (dict): Dictionary mapping file paths to file contents
            chapters (list): List of all chapter dictionaries
            
        Returns:
            str: The prompt for the LLM
        """
        prompt = f"""
        You are an expert code educator. Your task is to write a tutorial chapter explaining the '{abstraction["name"]}' component of a codebase.
        
        Write a comprehensive Markdown chapter that explains this component in detail. Your chapter should:
        
        1. Start with a clear title (# Chapter X: ComponentName)
        2. Provide an overview of the component's purpose and role in the system
        3. Explain its key responsibilities and features
        4. Include relevant code snippets with explanations
        5. Discuss how it interacts with other components
        6. Use proper Markdown formatting (headers, code blocks, lists, etc.)
        7. Include a section on best practices or common patterns related to this component
        8. Provide examples of how to use or extend this component
        
        Here is information about the component:
        
        """
        
        # Add abstraction details to the prompt
        prompt += json.dumps(abstraction, indent=2)
        
        # Add relationships to the prompt
        prompt += "\n\nRelationships with other components:\n\n"
        if relationships:
            # Group relationships by type
            relationships_by_type = {}
            for rel in relationships:
                rel_type = rel.get("type", "unknown")
                if rel_type not in relationships_by_type:
                    relationships_by_type[rel_type] = []
                relationships_by_type[rel_type].append(rel)
            
            # Add relationships by type
            for rel_type, rels in relationships_by_type.items():
                prompt += f"\n{rel_type.capitalize()} relationships:\n"
                prompt += json.dumps(rels, indent=2)
        else:
            prompt += "No direct relationships with other components."
        
        # Add file contents to the prompt
        prompt += "\n\nRelevant code files:\n\n"
        for file_path in abstraction.get("files", []):
            if file_path in files:
                content = files[file_path]
                # Limit content length to avoid token limits
                if len(content) > 3000:
                    content = content[:3000] + "... [truncated]"
                
                prompt += f"\n--- {file_path} ---\n"
                prompt += format_code_block(content, file_path.split(".")[-1])
        
        # Add information about other chapters for cross-referencing
        prompt += "\n\nOther chapters in the tutorial:\n\n"
        for chapter in chapters:
            if chapter["abstraction"]["name"] != abstraction["name"]:
                prompt += f"- Chapter {chapter['number']}: {chapter['abstraction']['name']} ({chapter['abstraction']['type']})\n"
        
        prompt += """
        
        Guidelines for writing the chapter:
        
        1. Be clear and concise, but thorough in your explanations
        2. Use code examples to illustrate key concepts
        3. Explain the code, don't just show it
        4. Use proper Markdown formatting for headers, code blocks, lists, etc.
        5. Make the content accessible to developers with intermediate experience
        6. Focus on practical understanding rather than theoretical concepts
        7. Highlight best practices and common patterns
        
        Write the complete Markdown chapter content:
        """
        
        return prompt
