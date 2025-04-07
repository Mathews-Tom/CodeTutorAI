"""
EnlightenAI - Formatting Utilities

This module provides utilities for formatting prompts and Markdown content.
"""

import re
import os
from typing import Dict, List, Any


def format_code_block(code: str, language: str = "") -> str:
    """Format code as a Markdown code block.
    
    Args:
        code (str): The code to format
        language (str, optional): The language for syntax highlighting
        
    Returns:
        str: Formatted Markdown code block
    """
    return f"```{language}\n{code}\n```"


def format_file_for_prompt(path: str, content: str, max_length: int = 5000) -> str:
    """Format a file for inclusion in an LLM prompt.
    
    Args:
        path (str): The file path
        content (str): The file content
        max_length (int, optional): Maximum content length
        
    Returns:
        str: Formatted file content for the prompt
    """
    # Truncate content if it's too long
    if len(content) > max_length:
        content = content[:max_length] + "... [truncated]"
    
    # Get the file extension for language detection
    _, ext = os.path.splitext(path)
    language = ext[1:] if ext else ""
    
    return f"File: {path}\n\n{format_code_block(content, language)}"


def format_abstraction_for_markdown(abstraction: Dict[str, Any]) -> str:
    """Format an abstraction as Markdown content.
    
    Args:
        abstraction (dict): The abstraction to format
        
    Returns:
        str: Formatted Markdown content
    """
    name = abstraction["name"]
    type_name = abstraction["type"]
    description = abstraction["description"]
    files = abstraction.get("files", [])
    responsibilities = abstraction.get("responsibilities", [])
    
    markdown = f"## {name}\n\n"
    markdown += f"**Type:** {type_name}\n\n"
    markdown += f"**Description:** {description}\n\n"
    
    if files:
        markdown += "**Defined in:**\n\n"
        for file_path in files:
            markdown += f"- `{file_path}`\n"
        markdown += "\n"
    
    if responsibilities:
        markdown += "**Key Responsibilities:**\n\n"
        for responsibility in responsibilities:
            markdown += f"- {responsibility}\n"
        markdown += "\n"
    
    return markdown


def create_mermaid_diagram(abstractions: List[Dict[str, Any]], relationships: List[Dict[str, Any]]) -> str:
    """Create a Mermaid diagram from abstractions and relationships.
    
    Args:
        abstractions (list): List of abstraction dictionaries
        relationships (list): List of relationship dictionaries
        
    Returns:
        str: Mermaid diagram code
    """
    mermaid = "```mermaid\ngraph TD\n"
    
    # Add nodes
    for abstraction in abstractions:
        node_id = re.sub(r'[^a-zA-Z0-9]', '', abstraction["name"])
        node_label = f"{abstraction['name']} ({abstraction['type']})"
        mermaid += f"    {node_id}[\"{node_label}\"]\n"
    
    # Add edges
    for relationship in relationships:
        source = re.sub(r'[^a-zA-Z0-9]', '', relationship["source"])
        target = re.sub(r'[^a-zA-Z0-9]', '', relationship["target"])
        rel_type = relationship["type"]
        
        # Use different arrow types based on relationship type
        arrow = "-->"
        if rel_type == "inherits":
            arrow = "-->|inherits|"
        elif rel_type == "uses":
            arrow = "-->|uses|"
        elif rel_type == "calls":
            arrow = "-->|calls|"
        elif rel_type == "imports":
            arrow = "-.->|imports|"
        
        mermaid += f"    {source} {arrow} {target}\n"
    
    mermaid += "```"
    return mermaid


def create_table_of_contents(chapters: List[Dict[str, Any]]) -> str:
    """Create a Markdown table of contents from chapter information.
    
    Args:
        chapters (list): List of chapter dictionaries
        
    Returns:
        str: Markdown table of contents
    """
    toc = "## Table of Contents\n\n"
    
    for i, chapter in enumerate(chapters):
        title = chapter["title"]
        filename = chapter.get("filename", f"chapter_{i+1}.md")
        toc += f"{i+1}. [{title}]({filename})\n"
    
    return toc
