"""
EnlightenAI - Fetch Repository Node

This module contains the FetchRepoNode class, which is responsible for
fetching files from a GitHub repository and storing them in the shared context.
"""

import base64
import os
import re
import subprocess
import tempfile
from fnmatch import fnmatch
from urllib.parse import urlparse

import requests

from nodes import Node


class FetchRepoNode(Node):
    """Node for fetching files from a GitHub repository."""

    def process(self, context):
        """Fetch files from the GitHub repository specified in the context.

        Args:
            context (dict): The shared context dictionary containing:
                - repo_url: The GitHub repository URL
                - include_patterns: List of file patterns to include
                - exclude_patterns: List of file patterns to exclude
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the fetched files.
        """
        repo_url = context["repo_url"]
        include_patterns = context["include_patterns"]
        exclude_patterns = context["exclude_patterns"]
        verbose = context.get("verbose", False)

        if verbose:
            print(f"Fetching repository: {repo_url}")
            print(f"Include patterns: {include_patterns}")
            print(f"Exclude patterns: {exclude_patterns}")

        # Fetch files from the repository
        try:
            # Try using the GitHub API first
            owner, repo = self._parse_github_url(repo_url)
            files = self._fetch_repo_files_api(
                owner=owner, repo=repo, api_key=context.get("api_key"), verbose=verbose
            )
        except Exception as e:
            if verbose:
                print(f"GitHub API failed: {str(e)}")
                print("Falling back to git clone...")

            # Fall back to cloning the repository
            owner, repo = self._parse_github_url(repo_url)
            files = self._fetch_repo_files_clone(
                owner=owner, repo=repo, verbose=verbose
            )

        # Filter files based on include/exclude patterns
        filtered_files = {}
        for path, content in files.items():
            # Check if the file matches any include pattern
            included = any(fnmatch(path, pattern) for pattern in include_patterns)

            # Check if the file matches any exclude pattern
            excluded = any(fnmatch(path, pattern) for pattern in exclude_patterns)

            if included and not excluded:
                filtered_files[path] = content
                if verbose:
                    print(f"Including file: {path}")
            elif verbose:
                print(f"Excluding file: {path}")

        # Update the context with the filtered files
        context["files"] = filtered_files

        if verbose:
            print(f"Fetched {len(filtered_files)} files from {repo_url}")

        # Return None as we've updated the context directly
        return None

    def _parse_github_url(self, repo_url):
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

    def _fetch_repo_files_api(self, owner, repo, api_key=None, verbose=False):
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
                    if content_data.get("encoding") == "base64" and content_data.get(
                        "content"
                    ):
                        try:
                            content = base64.b64decode(content_data["content"]).decode(
                                "utf-8"
                            )
                            files[path] = content
                        except UnicodeDecodeError:
                            if verbose:
                                print(f"Skipping binary file: {path}")
                elif verbose:
                    print(f"Failed to fetch {path}: {content_response.status_code}")

        return files

    def _fetch_repo_files_clone(self, owner, repo, verbose=False):
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
