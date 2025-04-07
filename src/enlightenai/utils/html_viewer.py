"""
EnlightenAI - HTML Viewer

This module provides functions for creating a browser-based viewer for tutorials.
"""

import os
import shutil
import webbrowser
from typing import Any, Dict, List, Optional


def create_html_viewer(
    output_dir: str,
    title: str,
    chapters: List[Dict[str, Any]],
    diagrams: Optional[Dict[str, str]] = None,
) -> str:
    """Create a browser-based viewer for the tutorial.

    Args:
        output_dir (str): Output directory for the tutorial
        title (str): Title of the tutorial
        chapters (list): List of chapter dictionaries
        diagrams (dict, optional): Dictionary of generated diagrams

    Returns:
        str: Path to the HTML file
    """
    # Create the viewer directory
    viewer_dir = os.path.join(output_dir, "viewer")
    os.makedirs(viewer_dir, exist_ok=True)

    # Create the assets directory
    assets_dir = os.path.join(viewer_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Create the CSS file
    css_path = os.path.join(assets_dir, "style.css")
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(_get_css())

    # Create the JavaScript file
    js_path = os.path.join(assets_dir, "script.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(_get_js())

    # Create the HTML file
    html_path = os.path.join(viewer_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(_get_html(title, chapters, diagrams))

    # Copy chapter files to the viewer directory
    chapters_dir = os.path.join(output_dir, "chapters")
    viewer_chapters_dir = os.path.join(viewer_dir, "chapters")
    os.makedirs(viewer_chapters_dir, exist_ok=True)

    # Create a default chapter if no chapters are available
    if not chapters:
        default_chapter_path = os.path.join(viewer_chapters_dir, "no_chapters.md")
        with open(default_chapter_path, "w", encoding="utf-8") as f:
            f.write(
                "# No Chapters Available\n\nNo chapters were generated for this repository. Please try again with different parameters."
            )
    else:
        for chapter in chapters:
            if "filename" in chapter:
                src_path = os.path.join(chapters_dir, chapter["filename"])
                dst_path = os.path.join(viewer_chapters_dir, chapter["filename"])
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)

    # Copy diagram files to the viewer directory if available
    if diagrams:
        diagrams_dir = os.path.join(output_dir, "diagrams")
        viewer_diagrams_dir = os.path.join(viewer_dir, "diagrams")
        os.makedirs(viewer_diagrams_dir, exist_ok=True)

        for diagram_type in diagrams:
            src_path = os.path.join(diagrams_dir, f"{diagram_type}.md")
            dst_path = os.path.join(viewer_diagrams_dir, f"{diagram_type}.md")
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)

    return html_path


def open_html_viewer(html_path: str) -> None:
    """Open the HTML viewer in the default web browser.

    Args:
        html_path (str): Path to the HTML file
    """
    webbrowser.open(f"file://{os.path.abspath(html_path)}")


def _get_html(
    title: str,
    chapters: List[Dict[str, Any]],
    diagrams: Optional[Dict[str, str]] = None,
) -> str:
    """Get the HTML content for the viewer.

    Args:
        title (str): Title of the tutorial
        chapters (list): List of chapter dictionaries
        diagrams (dict, optional): Dictionary of generated diagrams

    Returns:
        str: HTML content
    """
    # Create the table of contents
    toc_items = []
    if chapters:
        for chapter in chapters:
            if "filename" in chapter:
                toc_items.append(
                    f'<li><a href="#" data-chapter="{chapter["filename"]}">'
                    f"Chapter {chapter['number']}: {chapter['title']}</a></li>"
                )

    if toc_items:
        toc_html = "\n".join(toc_items)
    else:
        toc_html = "<li>No chapters available</li>"

    # Create the diagrams section if available
    diagrams_html = ""
    if diagrams:
        diagrams_html = """
        <div class="diagrams-section">
            <h2>Diagrams</h2>
            <ul>
        """
        for diagram_type in diagrams:
            display_name = diagram_type.replace("_", " ").title()
            diagrams_html += f'<li><a href="#" data-diagram="{diagram_type}.md">{display_name}</a></li>'
        diagrams_html += """
            </ul>
        </div>
        """

    # Create the HTML content
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="assets/style.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="logo">
                <h1>EnlightenAI</h1>
            </div>
            <div class="toc">
                <h2>Table of Contents</h2>
                <ul>
                    {toc_html}
                </ul>
            </div>
            {diagrams_html}
        </div>
        <div class="content">
            <div id="chapter-content">
                <h1>{title}</h1>
                <p>Select a chapter from the table of contents to begin.</p>
            </div>
        </div>
    </div>
    <script src="assets/script.js"></script>
</body>
</html>"""

    return html


def _get_css() -> str:
    """Get the CSS content for the viewer.

    Returns:
        str: CSS content
    """
    return """
:root {
    --primary-color: #4a6baf;
    --secondary-color: #f8f9fa;
    --text-color: #333;
    --link-color: #0366d6;
    --border-color: #e1e4e8;
    --sidebar-width: 300px;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: #fff;
}

.container {
    display: flex;
    min-height: 100vh;
}

.sidebar {
    width: var(--sidebar-width);
    background-color: var(--secondary-color);
    border-right: 1px solid var(--border-color);
    padding: 20px;
    overflow-y: auto;
    position: fixed;
    top: 0;
    bottom: 0;
}

.content {
    flex: 1;
    padding: 30px;
    margin-left: var(--sidebar-width);
    max-width: calc(100% - var(--sidebar-width));
}

.logo h1 {
    color: var(--primary-color);
    font-size: 24px;
    margin-bottom: 20px;
}

.toc h2, .diagrams-section h2 {
    font-size: 18px;
    margin-bottom: 10px;
    color: var(--primary-color);
}

.toc ul, .diagrams-section ul {
    list-style-type: none;
}

.toc li, .diagrams-section li {
    margin-bottom: 8px;
}

.toc a, .diagrams-section a {
    color: var(--link-color);
    text-decoration: none;
    display: block;
    padding: 5px 10px;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.toc a:hover, .diagrams-section a:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

.toc a.active, .diagrams-section a.active {
    background-color: rgba(0, 0, 0, 0.1);
    font-weight: bold;
}

#chapter-content {
    max-width: 800px;
    margin: 0 auto;
}

#chapter-content h1 {
    font-size: 32px;
    margin-bottom: 20px;
    color: var(--primary-color);
}

#chapter-content h2 {
    font-size: 24px;
    margin-top: 30px;
    margin-bottom: 15px;
    padding-bottom: 5px;
    border-bottom: 1px solid var(--border-color);
}

#chapter-content h3 {
    font-size: 20px;
    margin-top: 25px;
    margin-bottom: 10px;
}

#chapter-content p {
    margin-bottom: 15px;
}

#chapter-content code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    background-color: rgba(0, 0, 0, 0.05);
    padding: 2px 4px;
    border-radius: 3px;
}

#chapter-content pre {
    background-color: #f6f8fa;
    border-radius: 6px;
    padding: 16px;
    overflow: auto;
    margin-bottom: 16px;
}

#chapter-content pre code {
    background-color: transparent;
    padding: 0;
}

#chapter-content a {
    color: var(--link-color);
    text-decoration: none;
}

#chapter-content a:hover {
    text-decoration: underline;
}

#chapter-content ul, #chapter-content ol {
    margin-bottom: 15px;
    padding-left: 25px;
}

#chapter-content li {
    margin-bottom: 5px;
}

#chapter-content img {
    max-width: 100%;
    height: auto;
    margin: 20px 0;
}

#chapter-content blockquote {
    border-left: 4px solid var(--primary-color);
    padding-left: 16px;
    margin-left: 0;
    margin-bottom: 16px;
    color: #6a737d;
}

.diagrams-section {
    margin-top: 30px;
}

@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }

    .sidebar {
        width: 100%;
        position: static;
        border-right: none;
        border-bottom: 1px solid var(--border-color);
    }

    .content {
        margin-left: 0;
        max-width: 100%;
    }
}
"""


def _get_js() -> str:
    """Get the JavaScript content for the viewer.

    Returns:
        str: JavaScript content
    """
    return """
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Mermaid
    mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose'
    });

    // Get elements
    const chapterLinks = document.querySelectorAll('.toc a');
    const diagramLinks = document.querySelectorAll('.diagrams-section a');
    const chapterContent = document.getElementById('chapter-content');

    // Add click event listeners to chapter links
    chapterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active class from all links
            chapterLinks.forEach(l => l.classList.remove('active'));
            diagramLinks.forEach(l => l.classList.remove('active'));

            // Add active class to clicked link
            this.classList.add('active');

            // Get chapter filename
            const chapterFile = this.getAttribute('data-chapter');

            // Load chapter content
            fetch(`chapters/${chapterFile}`)
                .then(response => response.text())
                .then(markdown => {
                    // Render markdown
                    chapterContent.innerHTML = marked.parse(markdown);

                    // Render Mermaid diagrams
                    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                })
                .catch(error => {
                    console.error('Error loading chapter:', error);
                    chapterContent.innerHTML = '<h1>Error</h1><p>Failed to load chapter content.</p>';
                });
        });
    });

    // Add click event listeners to diagram links
    diagramLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active class from all links
            chapterLinks.forEach(l => l.classList.remove('active'));
            diagramLinks.forEach(l => l.classList.remove('active'));

            // Add active class to clicked link
            this.classList.add('active');

            // Get diagram filename
            const diagramFile = this.getAttribute('data-diagram');

            // Load diagram content
            fetch(`diagrams/${diagramFile}`)
                .then(response => response.text())
                .then(markdown => {
                    // Render markdown
                    chapterContent.innerHTML = marked.parse(markdown);

                    // Render Mermaid diagrams
                    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
                })
                .catch(error => {
                    console.error('Error loading diagram:', error);
                    chapterContent.innerHTML = '<h1>Error</h1><p>Failed to load diagram content.</p>';
                });
        });
    });

    // Load the first chapter by default if available
    if (chapterLinks.length > 0) {
        chapterLinks[0].click();
    } else {
        // If no chapters are available, load the default chapter
        fetch('chapters/no_chapters.md')
            .then(response => response.text())
            .then(markdown => {
                // Render markdown
                chapterContent.innerHTML = marked.parse(markdown);
            })
            .catch(error => {
                console.error('Error loading default chapter:', error);
                chapterContent.innerHTML = '<h1>No Chapters Available</h1><p>No chapters were generated for this repository. Please try again with different parameters.</p>';
            });
    }
});
"""
