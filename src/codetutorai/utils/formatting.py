"""
CodeTutorAI - Formatting Utilities

This module provides utilities for formatting text and code.
"""

import re
from typing import Any, Dict, List, Optional



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
            result.append(f"{i + 1}. {item}")
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

    return text[: max_length - len(ellipsis)] + ellipsis


def get_repo_info_from_url(url: str) -> Optional[Dict[str, str]]:
    """
    Extracts the username and repository name from a GitHub URL.

    Args:
        url (str): The GitHub repository URL.

    Returns:
        Optional[Dict[str, str]]: A dictionary with 'username' and 'repo_name',
                                    or None if the URL is invalid.
    """
    if not url:
        return None
    # Regex to capture username and repo name from various GitHub URL formats
    # Handles optional .git suffix and trailing slashes
    match = re.match(
        r"^(?:https?://|git@)github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?/?$", url
    )
    if match:
        username = match.group(1)
        repo_name = match.group(2)
        return {"username": username, "repo_name": repo_name}
    return None


def is_valid_github_url(url: str) -> bool:
    """Check if the provided string is a valid GitHub repository URL."""
    if not url:
        return False
    # Basic check for GitHub repo URL structure
    pattern = r"^https://github\.com/[^/]+/[^/]+/?$"
    # Ensure re is imported (it should be at the top of the file)
    return bool(re.match(pattern, url))


def format_duration(seconds: float) -> str:
    """Formats a duration in seconds into HH hr MM min SS s format."""
    if seconds < 0:
        return "0s"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}hr")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts: # Always show seconds if non-zero or if H/M are zero
        parts.append(f"{secs}s")

    return " ".join(parts)
# Common Mermaid keywords (add more if needed)
MERMAID_KEYWORDS = {
    "graph", "subgraph", "end", "classDiagram", "stateDiagram", "sequenceDiagram",
    "gantt", "pie", "flowchart", "class", "state", "style", "link", "click",
    "direction", "TB", "BT", "RL", "LR", "TD", "participant", "actor", "note",
    "loop", "alt", "opt", "par", "critical", "break", "rect", "circle", "ellipse",
    "diamond", "hexagon", "roundrect", "label", "arrowhead", "arrowtail",
    "line", "stroke", "fill", "color", "font", "align", "width", "height",
    "margin", "padding", "border", "background", "foreground", "text", "title",
    "section", "dateFormat", "axisFormat", "tickInterval", "excludes", "includes",
    "todayMarker", "theme", "securityLevel", "startOnLoad", "htmlLabels",
    "nodeSpacing", "rankSpacing", "curve", "stepBefore", "stepAfter", "basis",
    "linear", "cardinal", "catmullRom", "monotoneX", "monotoneY", "natural",
    "%%", "---", "-->", "--", "->", "-.", "-.->", "==>", "==", "<--", "<-", "<->",
    "<-->", "o--", "--o", "x--", "--x", "<<--", "-->>", "o->", "<-o", "x->", "<-x",
    "..>", "<..", "..", ".."
}

def sanitize_mermaid_label(label: str) -> str:
    """Removes or replaces potentially problematic characters for Mermaid IDs/labels.

    Keeps alphanumeric characters and underscores. Replaces others with an underscore.
    Ensures the ID starts with a letter (prepends 'cls_' if needed).
    Prevents labels starting/ending with underscores unless original did.
    Appends '_' if the sanitized label matches a Mermaid keyword.
    Ensures the label is not empty.
    """
    if not label:
        return "cls_unknown" # Return a valid default ID

    original_label = label # Keep original for start/end underscore check

    # Replace sequences of non-alphanumeric (excluding underscore) with a single underscore
    sanitized = re.sub(r'[^\w]+', '_', label)

    # Remove leading/trailing underscores unless the original label had them
    if not original_label.startswith('_') and sanitized.startswith('_'):
        sanitized = sanitized.lstrip('_')
    if not original_label.endswith('_') and sanitized.endswith('_'):
        sanitized = sanitized.rstrip('_')

    # Ensure the result is not empty after stripping
    if not sanitized:
        return "cls_empty" # Return a valid default ID if sanitization results in empty

    # Ensure the ID starts with a letter
    if not sanitized[0].isalpha():
        sanitized = "cls_" + sanitized

    # Check against keywords (case-insensitive check, but append to original case)
    if sanitized.lower() in MERMAID_KEYWORDS:
        sanitized += "_"

    return sanitized
