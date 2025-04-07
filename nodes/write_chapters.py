"""
EnlightenAI - Write Chapters Node

This module contains the WriteChaptersNode class, which is responsible for
generating Markdown content for each chapter in the tutorial.
"""

import os
import json
from nodes import Node
from utils.call_llm import call_llm
from utils.formatting import format_code_block


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
                - verbose: Whether to print verbose output
                
        Returns:
            None: The context is updated directly with the generated chapters.
        """
        files = context["files"]
        chapters = context["chapters"]
        relationships = context["relationships"]
        output_dir = context["output_dir"]
        verbose = context.get("verbose", False)
        
        # Create the chapters directory if it doesn't exist
        chapters_dir = os.path.join(output_dir, "chapters")
        os.makedirs(chapters_dir, exist_ok=True)
        
        if verbose:
            print(f"Generating content for {len(chapters)} chapters")
        
        # Generate content for each chapter
        for chapter in chapters:
            if verbose:
                print(f"Generating content for chapter {chapter['number']}: {chapter['title']}")
            
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
            
            # Save the chapter content to a file
            chapter_path = os.path.join(chapters_dir, chapter["filename"])
            with open(chapter_path, "w") as f:
                f.write(llm_response)
            
            # Add the content to the chapter dictionary
            chapter["content"] = llm_response
            
            if verbose:
                print(f"Saved chapter to {chapter_path}")
        
        # Return None as we've updated the context directly
        return None
    
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
        
        Here is information about the component:
        
        """
        
        # Add abstraction details to the prompt
        prompt += json.dumps(abstraction, indent=2)
        
        # Add relationships to the prompt
        prompt += "\n\nRelationships with other components:\n\n"
        if relationships:
            prompt += json.dumps(relationships, indent=2)
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
        
        prompt += "\n\nWrite the complete Markdown chapter content:"
        
        return prompt
