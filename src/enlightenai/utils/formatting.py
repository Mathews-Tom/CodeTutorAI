"""
EnlightenAI - Formatting Utilities

This module provides utilities for formatting text and code.
"""

import re
from typing import Dict, List, Any, Optional


def format_code_block(code: str, language: str = "") -> str:
    """Format code as a Markdown code block.
    
    Args:
        code (str): The code to format
        language (str, optional): The language of the code
        
    Returns:
        str: The formatted code block
    """
    return f"```{language}\n{code}\n```"


def format_file_path(file_path: str) -> str:
    """Format a file path for display.
    
    Args:
        file_path (str): The file path to format
        
    Returns:
        str: The formatted file path
    """
    return f"`{file_path}`"


def format_heading(text: str, level: int = 1) -> str:
    """Format text as a Markdown heading.
    
    Args:
        text (str): The text to format
        level (int, optional): The heading level (1-6)
        
    Returns:
        str: The formatted heading
    """
    level = max(1, min(level, 6))
    return f"{'#' * level} {text}"


def format_list(items: List[str], ordered: bool = False) -> str:
    """Format a list of items as a Markdown list.
    
    Args:
        items (list): The list of items to format
        ordered (bool, optional): Whether to use an ordered list
        
    Returns:
        str: The formatted list
    """
    if not items:
        return ""
    
    result = []
    for i, item in enumerate(items):
        if ordered:
            result.append(f"{i+1}. {item}")
        else:
            result.append(f"- {item}")
    
    return "\n".join(result)


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format data as a Markdown table.
    
    Args:
        headers (list): The table headers
        rows (list): The table rows
        
    Returns:
        str: The formatted table
    """
    if not headers or not rows:
        return ""
    
    # Create the header row
    result = [" | ".join(headers)]
    
    # Create the separator row
    separator = ["-" * len(header) for header in headers]
    result.append(" | ".join(separator))
    
    # Create the data rows
    for row in rows:
        result.append(" | ".join(row))
    
    return "\n".join(result)


def format_link(text: str, url: str) -> str:
    """Format text as a Markdown link.
    
    Args:
        text (str): The link text
        url (str): The link URL
        
    Returns:
        str: The formatted link
    """
    return f"[{text}]({url})"


def format_image(alt_text: str, url: str) -> str:
    """Format an image as Markdown.
    
    Args:
        alt_text (str): The image alt text
        url (str): The image URL
        
    Returns:
        str: The formatted image
    """
    return f"![{alt_text}]({url})"


def format_blockquote(text: str) -> str:
    """Format text as a Markdown blockquote.
    
    Args:
        text (str): The text to format
        
    Returns:
        str: The formatted blockquote
    """
    lines = text.split("\n")
    return "\n".join([f"> {line}" for line in lines])


def format_mermaid_diagram(diagram: str) -> str:
    """Format a Mermaid diagram as Markdown.
    
    Args:
        diagram (str): The Mermaid diagram code
        
    Returns:
        str: The formatted diagram
    """
    return f"```mermaid\n{diagram}\n```"


def sanitize_filename(filename: str) -> str:
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


def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
    """Truncate text to a maximum length.
    
    Args:
        text (str): The text to truncate
        max_length (int, optional): The maximum length
        ellipsis (str, optional): The ellipsis to append
        
    Returns:
        str: The truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(ellipsis)] + ellipsis
