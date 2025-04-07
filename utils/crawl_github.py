"""
EnlightenAI - GitHub Repository Crawler

This module provides utilities for fetching files from GitHub repositories
using the GitHub API or git clone.
"""

import os
import re
import tempfile
import subprocess
import base64
import requests
from urllib.parse import urlparse


def parse_github_url(repo_url):
    """Parse a GitHub URL into owner and repo name.
    
    Args:
        repo_url (str): GitHub repository URL
            (e.g., https://github.com/username/repo)
            
    Returns:
        tuple: (owner, repo_name)
    """
    # Handle URLs with or without .git extension
    url_path = urlparse(repo_url).path.strip("/")
    if url_path.endswith(".git"):
        url_path = url_path[:-4]
    
    parts = url_path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    
    return parts[0], parts[1]


def fetch_repo_files_api(owner, repo, api_key=None, verbose=False):
    """Fetch repository files using the GitHub API.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        api_key (str, optional): GitHub API key for authentication
        verbose (bool, optional): Whether to print verbose output
        
    Returns:
        dict: Dictionary mapping file paths to file contents
    """
    headers = {}
    if api_key:
        headers["Authorization"] = f"token {api_key}"
    
    # Get the default branch
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(repo_url, headers=headers)
    response.raise_for_status()
    default_branch = response.json()["default_branch"]
    
    if verbose:
        print(f"Default branch: {default_branch}")
    
    # Get the repository contents
    contents_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    response = requests.get(contents_url, headers=headers)
    response.raise_for_status()
    
    # Extract file paths
    files = {}
    for item in response.json()["tree"]:
        if item["type"] == "blob":
            path = item["path"]
            if verbose:
                print(f"Fetching file: {path}")
            
            # Get the file content
            content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={default_branch}"
            content_response = requests.get(content_url, headers=headers)
            
            if content_response.status_code == 200:
                content_data = content_response.json()
                if content_data.get("encoding") == "base64" and content_data.get("content"):
                    try:
                        content = base64.b64decode(content_data["content"]).decode("utf-8")
                        files[path] = content
                    except UnicodeDecodeError:
                        if verbose:
                            print(f"Skipping binary file: {path}")
            elif verbose:
                print(f"Failed to fetch {path}: {content_response.status_code}")
    
    return files


def fetch_repo_files_clone(owner, repo, verbose=False):
    """Fetch repository files by cloning the repository.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        verbose (bool, optional): Whether to print verbose output
        
    Returns:
        dict: Dictionary mapping file paths to file contents
    """
    # Create a temporary directory for the clone
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_url = f"https://github.com/{owner}/{repo}.git"
        
        if verbose:
            print(f"Cloning repository: {repo_url}")
            clone_cmd = ["git", "clone", repo_url, temp_dir]
        else:
            clone_cmd = ["git", "clone", "--quiet", repo_url, temp_dir]
        
        # Clone the repository
        subprocess.run(clone_cmd, check=True)
        
        # Walk the directory and read all files
        files = {}
        for root, _, filenames in os.walk(temp_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # Skip .git directory
                if ".git/" in rel_path or rel_path.startswith(".git"):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    files[rel_path] = content
                    if verbose:
                        print(f"Read file: {rel_path}")
                except (UnicodeDecodeError, IOError):
                    if verbose:
                        print(f"Skipping binary file: {rel_path}")
        
        return files


def fetch_repo_files(repo_url, api_key=None, verbose=False):
    """Fetch files from a GitHub repository.
    
    This function tries to use the GitHub API first, and falls back to
    cloning the repository if the API fails or if the repository is too large.
    
    Args:
        repo_url (str): GitHub repository URL
        api_key (str, optional): GitHub API key for authentication
        verbose (bool, optional): Whether to print verbose output
        
    Returns:
        dict: Dictionary mapping file paths to file contents
    """
    owner, repo = parse_github_url(repo_url)
    
    if verbose:
        print(f"Fetching repository: {owner}/{repo}")
    
    try:
        # Try using the GitHub API first
        return fetch_repo_files_api(owner, repo, api_key, verbose)
    except Exception as e:
        if verbose:
            print(f"GitHub API failed: {str(e)}")
            print("Falling back to git clone...")
        
        # Fall back to cloning the repository
        return fetch_repo_files_clone(owner, repo, verbose)
