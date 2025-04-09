"""
CodeTutorAI - Fetch Web Node

This module contains the FetchWebNode class for fetching web content related to a repository.
"""

import json
import os
from typing import Any, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from codetutorai.nodes.node import Node


class FetchWebNode(Node):
    """Node for fetching web content related to a repository."""

    def process(self, context):
        """Fetch web content related to a repository.
        
        Args:
            context (dict): The shared context dictionary containing:
                - web_url: URL of the website to fetch
                - repo_name: Name of the repository
                - output_dir: Output directory for the tutorial
                - verbose: Whether to print verbose output
                
        Returns:
            dict: Dictionary containing the web content.
        """
        verbose = context.get("verbose", False)
        web_url = context.get("web_url")
        repo_name = context.get("repo_name", "")
        output_dir = context.get("output_dir", "tutorial_output")
        
        if not web_url:
            if verbose:
                print("No web URL provided, skipping web content fetching")
            return {"web_content": {}}
        
        if verbose:
            print(f"Fetching web content from: {web_url}")
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Fetch the web content
        web_content = self._fetch_web_content(web_url, verbose)
        
        if verbose:
            print(f"Found {len(web_content)} pages of web content")
        
        # Save the web content to a file
        web_content_path = os.path.join(output_dir, "web_content.json")
        with open(web_content_path, "w", encoding="utf-8") as f:
            json.dump(web_content, f, indent=2)
        
        if verbose:
            print(f"Saved web content to {web_content_path}")
        
        # Update the context
        return {"web_content": web_content}
    
    def _fetch_web_content(self, web_url: str, verbose: bool) -> Dict[str, Dict[str, str]]:
        """Fetch web content from a URL.
        
        Args:
            web_url (str): URL of the website to fetch
            verbose (bool): Whether to print verbose output
            
        Returns:
            dict: Dictionary mapping page URLs to page content
        """
        # Parse the URL to get the domain
        parsed_url = urlparse(web_url)
        domain = parsed_url.netloc
        
        # Fetch the website
        try:
            if verbose:
                print(f"Fetching {web_url}...")
            
            # Use requests to fetch the website
            response = requests.get(web_url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract the title and content
            title = soup.title.string if soup.title else ""
            
            # Extract the main content
            content = ""
            main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
            if main_content:
                content = main_content.get_text(separator="\n", strip=True)
            else:
                # Fall back to the body
                content = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
            
            # Create the web content dictionary
            web_content = {
                web_url: {
                    "title": title,
                    "content": content
                }
            }
            
            if verbose:
                print(f"Fetched {web_url} successfully")
            
            return web_content
        except Exception as e:
            if verbose:
                print(f"Error fetching {web_url}: {str(e)}")
            return {}
