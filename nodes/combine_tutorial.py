"""
EnlightenAI - Combine Tutorial Node

This module contains the CombineTutorialNode class, which is responsible for
combining all chapters into a complete tutorial and generating an index file.
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from nodes import Node
from utils.call_llm import call_llm
from utils.formatting import create_table_of_contents, format_markdown


class CombineTutorialNode(Node):
    """Node for combining all chapters into a complete tutorial."""

    def process(self, context):
        """Combine all chapters into a complete tutorial and generate an index file.
        
        Args:
            context (dict): The shared context dictionary containing:
                - repo_url: The GitHub repository URL
                - abstractions: List of abstraction dictionaries
                - relationships: List of relationship dictionaries
                - chapters: List of chapter dictionaries
                - output_dir: Output directory for the tutorial
                - output_formats: List of output formats ("markdown", "html", "pdf", "github_pages")
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                
        Returns:
            None: The context is updated directly.
        """
        repo_url = context["repo_url"]
        abstractions = context["abstractions"]
        relationships = context["relationships"]
        chapters = context["chapters"]
        output_dir = context["output_dir"]
        output_formats = context.get("output_formats", ["markdown"])
        verbose = context.get("verbose", False)
        
        # Skip if no chapters were generated
        if not chapters:
            if verbose:
                print("No chapters to combine. Skipping tutorial compilation.")
            return None
        
        if verbose:
            print("Combining chapters into a complete tutorial")
        
        # Create the index file content
        index_content = self._create_index_content(
            repo_url, abstractions, relationships, chapters, context
        )
        
        # Save the index file
        index_path = os.path.join(output_dir, "index.md")
        with open(index_path, "w") as f:
            f.write(index_content)
        
        if verbose:
            print(f"Saved index file to {index_path}")
        
        # Generate additional output formats
        with tqdm(total=len(output_formats), desc="Generating output formats", disable=not verbose) as pbar:
            for output_format in output_formats:
                if output_format == "markdown":
                    # Already generated
                    pass
                elif output_format == "html":
                    self._generate_html(context, index_content)
                elif output_format == "pdf":
                    self._generate_pdf(context, index_content)
                elif output_format == "github_pages":
                    self._setup_github_pages(context)
                
                pbar.update(1)
        
        # Return None as we've updated the context directly
        return None
        
    def _generate_html(self, context, index_content):
        """Generate a single-page HTML version of the tutorial.
        
        Args:
            context (dict): The shared context dictionary
            index_content (str): The content of the index file
        """
        output_dir = context["output_dir"]
        chapters = context["chapters"]
        verbose = context.get("verbose", False)
        
        # Create the HTML directory
        html_dir = os.path.join(output_dir, "html")
        os.makedirs(html_dir, exist_ok=True)
        
        # Create the HTML template
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <meta name="description" content="{description}">
            <meta name="generator" content="EnlightenAI">
            <meta name="date" content="{date}">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3, h4, h5, h6 {{ margin-top: 1.5em; margin-bottom: 0.5em; }}
                h1 {{ font-size: 2.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                h2 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
                h3 {{ font-size: 1.5em; }}
                h4 {{ font-size: 1.25em; }}
                p {{ margin-top: 0; margin-bottom: 16px; }}
                code {{ font-family: SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace; padding: 0.2em 0.4em; background-color: rgba(27, 31, 35, 0.05); border-radius: 3px; }}
                pre {{ background-color: #f6f8fa; border-radius: 3px; padding: 16px; overflow: auto; }}
                pre code {{ background-color: transparent; padding: 0; }}
                a {{ color: #0366d6; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; }}
                table th, table td {{ padding: 6px 13px; border: 1px solid #dfe2e5; }}
                table th {{ font-weight: 600; }}
                img {{ max-width: 100%; }}
                blockquote {{ margin: 0; padding: 0 1em; color: #6a737d; border-left: 0.25em solid #dfe2e5; }}
                hr {{ height: 0.25em; padding: 0; margin: 24px 0; background-color: #e1e4e8; border: 0; }}
                .mermaid {{ text-align: center; }}
                .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #eaecef; color: #6a737d; font-size: 0.9em; text-align: center; }}
            </style>
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <script>mermaid.initialize({{startOnLoad:true}});</script>
        </head>
        <body>
            {content}
            <div class="footer">
                <p>Generated by <a href="https://github.com/Mathews-Tom/EnlightenAI">EnlightenAI</a> on {date}</p>
            </div>
        </body>
        </html>
        """
        
        # Extract the repository name from the context
        repo_url = context["repo_url"]
        repo_name = repo_url.rstrip("/").split("/")[-1]
        
        # Create a single HTML file with all content
        all_content = index_content
        
        # Add chapter content
        for chapter in sorted(chapters, key=lambda c: c["number"]):
            chapter_content = chapter.get("content", "")
            if chapter_content:
                all_content += f"\n\n---\n\n{chapter_content}"
        
        # Convert Markdown to HTML (basic conversion)
        html_content = self._markdown_to_html(all_content)
        
        # Fill in the template
        html = html_template.format(
            title=f"{repo_name} - Code Walkthrough",
            description=f"A comprehensive guide to the {repo_name} codebase",
            date=datetime.now().strftime("%Y-%m-%d"),
            content=html_content
        )
        
        # Save the HTML file
        html_path = os.path.join(html_dir, "index.html")
        with open(html_path, "w") as f:
            f.write(html)
        
        if verbose:
            print(f"Saved HTML version to {html_path}")
    
    def _generate_pdf(self, context, index_content):
        """Generate a PDF version of the tutorial.
        
        Args:
            context (dict): The shared context dictionary
            index_content (str): The content of the index file
        """
        output_dir = context["output_dir"]
        verbose = context.get("verbose", False)
        
        # Create the PDF directory
        pdf_dir = os.path.join(output_dir, "pdf")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Create a PDF-ready Markdown file
        pdf_markdown_path = os.path.join(pdf_dir, "tutorial.md")
        with open(pdf_markdown_path, "w") as f:
            f.write(index_content)
            
            # Add chapter content
            for chapter in sorted(context["chapters"], key=lambda c: c["number"]):
                chapter_content = chapter.get("content", "")
                if chapter_content:
                    f.write(f"\n\n---\n\n{chapter_content}")
        
        if verbose:
            print(f"Saved PDF-ready Markdown to {pdf_markdown_path}")
            print("To convert to PDF, use a tool like 'pandoc' or a Markdown-to-PDF converter")
    
    def _setup_github_pages(self, context):
        """Set up GitHub Pages configuration.
        
        Args:
            context (dict): The shared context dictionary
        """
        output_dir = context["output_dir"]
        verbose = context.get("verbose", False)
        
        # Create the docs directory (GitHub Pages uses /docs by default)
        docs_dir = os.path.join(output_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Copy all Markdown files to the docs directory
        for file in os.listdir(output_dir):
            if file.endswith(".md"):
                shutil.copy(os.path.join(output_dir, file), os.path.join(docs_dir, file))
        
        # Copy the chapters directory
        chapters_dir = os.path.join(output_dir, "chapters")
        if os.path.exists(chapters_dir):
            docs_chapters_dir = os.path.join(docs_dir, "chapters")
            os.makedirs(docs_chapters_dir, exist_ok=True)
            for file in os.listdir(chapters_dir):
                if file.endswith(".md"):
                    shutil.copy(os.path.join(chapters_dir, file), os.path.join(docs_chapters_dir, file))
        
        # Create a _config.yml file for GitHub Pages
        config_yml = """
        remote_theme: pages-themes/cayman@v0.2.0
        plugins:
        - jekyll-remote-theme
        title: {title}
        description: {description}
        show_downloads: false
        """
        
        # Extract the repository name from the context
        repo_url = context["repo_url"]
        repo_name = repo_url.rstrip("/").split("/")[-1]
        
        # Fill in the template
        config_yml = config_yml.format(
            title=f"{repo_name} - Code Walkthrough",
            description=f"A comprehensive guide to the {repo_name} codebase"
        )
        
        # Save the _config.yml file
        config_path = os.path.join(docs_dir, "_config.yml")
        with open(config_path, "w") as f:
            f.write(config_yml)
        
        if verbose:
            print(f"Set up GitHub Pages configuration in {docs_dir}")
    
    def _markdown_to_html(self, markdown):
        """Convert Markdown to HTML (basic conversion).
        
        Args:
            markdown (str): The Markdown content
            
        Returns:
            str: The HTML content
        """
        html = markdown
        
        # Convert headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Convert paragraphs (simple approach)
        html = re.sub(r'([^\n])(\n)([^\n#])', r'\1<br>\3', html)
        
        # Convert links
        html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Convert code blocks (preserve Mermaid blocks)
        html = re.sub(r'```mermaid\n(.+?)\n```', r'<div class="mermaid">\1</div>', html, flags=re.DOTALL)
        html = re.sub(r'```(\w*)\n(.+?)\n```', r'<pre><code class="language-\1">\2</code></pre>', html, flags=re.DOTALL)
        
        # Convert inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # Convert lists (simple approach)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        return html
    
    def _create_index_content(
        self, repo_url, abstractions, _relationships, chapters, context
    ):
        """Create the content for the index file.
        
        Args:
            repo_url (str): The GitHub repository URL
            abstractions (list): List of abstraction dictionaries
            _relationships (list): List of relationship dictionaries (unused)
            chapters (list): List of chapter dictionaries
            context (dict): The shared context dictionary
            
        Returns:
            str: The content for the index file
        """
        # Extract the repository name from the URL
        repo_name = repo_url.rstrip("/").split("/")[-1]
        
        # Create the LLM prompt for the overview
        prompt = f"""
        You are an expert code educator. Your task is to write a concise overview of the '{repo_name}' codebase.
        
        Write a brief Markdown overview (about 3-5 paragraphs) that explains:
        1. What the project does
        2. Its main features and capabilities
        3. The overall architecture and design philosophy
        
        Here is information about the key components in the codebase:
        
        """
        
        # Add abstraction details to the prompt
        prompt += json.dumps(abstractions, indent=2)
        
        # Call the LLM to generate the overview
        overview = call_llm(
            prompt=prompt,
            provider=context.get("llm_provider", "openai"),
            api_key=context.get("api_key"),
            max_tokens=1000,
            temperature=0.5
        )
        
        # Get the Mermaid diagram from the context
        diagram = context.get("mermaid_diagram", "```mermaid\nflowchart TD\n    No_Diagram[\"No diagram available\"]\n```")
        
        # Create the table of contents
        toc = create_table_of_contents(chapters)
        
        # Combine everything into the index content
        index_content = f"""# {repo_name} - Code Walkthrough

## Overview

{overview}

## System Architecture

The following diagram shows the key components and their relationships:

{diagram}

{toc}

---

*This tutorial was generated by [EnlightenAI](https://github.com/Mathews-Tom/EnlightenAI), an intelligent codebase explainer.*
"""
        
        return index_content
