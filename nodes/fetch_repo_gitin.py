"""
EnlightenAI - Fetch Repository Node using gitin

This module contains the FetchRepoGitinNode class, which is responsible for
fetching files from a GitHub repository using the gitin package and storing them in the shared context.
"""

import json
import os
import re
import subprocess
import tempfile
from fnmatch import fnmatch
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from nodes import Node


class FetchRepoGitinNode(Node):
    """Node for fetching files from a GitHub repository using gitin."""

    def process(self, context):
        """Fetch files from the GitHub repository specified in the context using gitin.

        Args:
            context (dict): The shared context dictionary containing:
                - repo_url: The GitHub repository URL
                - include_patterns: List of file patterns to include
                - exclude_patterns: List of file patterns to exclude
                - max_file_size: Maximum file size in bytes (default: 1MB)
                - fetch_repo_metadata: Whether to fetch repository metadata (default: True)
                - api_key: GitHub API key for authentication (optional)
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the fetched files and metadata.
        """
        repo_url = context["repo_url"]
        include_patterns = context["include_patterns"]
        exclude_patterns = context["exclude_patterns"]
        max_file_size = context.get("max_file_size", 1024 * 1024)  # Default: 1MB
        fetch_repo_metadata = context.get("fetch_repo_metadata", True)
        api_key = context.get("api_key")
        verbose = context.get("verbose", False)

        if verbose:
            print(f"Fetching repository: {repo_url}")
            print(f"Include patterns: {include_patterns}")
            print(f"Exclude patterns: {exclude_patterns}")
            print(f"Max file size: {max_file_size} bytes")

        # Parse the repository URL to extract owner and repo name
        owner, repo_name = self._parse_github_url(repo_url)

        # Fetch repository metadata if requested
        if fetch_repo_metadata:
            try:
                repo_metadata = self._fetch_repo_metadata(owner, repo_name, api_key)
                context["repo_metadata"] = repo_metadata
                if verbose:
                    print(f"Repository: {repo_metadata['full_name']}")
                    print(f"Description: {repo_metadata['description']}")
                    print(f"Stars: {repo_metadata['stargazers_count']}")
                    print(f"Forks: {repo_metadata['forks_count']}")
                    print(f"Default branch: {repo_metadata['default_branch']}")
            except Exception as e:
                if verbose:
                    print(f"Warning: Failed to fetch repository metadata: {str(e)}")
                context["repo_metadata"] = {}

        # Create a temporary file to store the gitin output
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
            temp_output_path = temp_file.name

        try:
            # Prepare the gitin command
            include_arg = ",".join(include_patterns) if include_patterns else "*"
            exclude_arg = ",".join(exclude_patterns) if exclude_patterns else ""

            cmd = ["gitin", repo_url, "-o", temp_output_path]

            if include_arg:
                cmd.extend(["--include", include_arg])

            if exclude_arg:
                cmd.extend(["--exclude", exclude_arg])

            # Add GitHub token if provided
            if api_key:
                cmd.extend(["--token", api_key])

            # Run gitin to fetch the repository
            if verbose:
                print(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "rate limit exceeded" in error_msg.lower():
                    raise Exception(
                        "GitHub API rate limit exceeded. Please provide a GitHub API token or try again later."
                    )
                else:
                    raise Exception(f"gitin failed: {error_msg}")

            # Parse the markdown file to extract file contents with progress bar
            files = self._parse_gitin_output(temp_output_path, max_file_size, verbose)

            # Update the context with the files
            context["files"] = files

            if verbose:
                print(f"Fetched {len(files)} files from {repo_url}")

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)

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

    def _fetch_repo_metadata(self, owner, repo, api_key=None):
        """Fetch repository metadata from GitHub API.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            api_key (str, optional): GitHub API key for authentication

        Returns:
            dict: Repository metadata
        """
        headers = {}
        if api_key:
            headers["Authorization"] = f"token {api_key}"

        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(repo_url, headers=headers)
        response.raise_for_status()

        return response.json()

    def _parse_gitin_output(self, markdown_path, max_file_size=None, verbose=False):
        """Parse the gitin output markdown file to extract file contents.

        Args:
            markdown_path (str): Path to the markdown file generated by gitin
            max_file_size (int, optional): Maximum file size in bytes
            verbose (bool, optional): Whether to print verbose output

        Returns:
            dict: Dictionary mapping file paths to file contents
        """
        files = {}
        current_file = None
        content_lines = []

        with open(markdown_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Create a progress bar for parsing files
        with tqdm(
            total=len(lines), desc="Parsing files", unit="line", disable=not verbose
        ) as pbar:
            in_code_block = False

            for line in lines:
                # Update the progress bar
                pbar.update(1)

                # Check for file headers (typically formatted as "### path/to/file.ext")
                if line.startswith("### "):
                    # If we were processing a file, save it
                    if current_file and content_lines:
                        content = "".join(content_lines)

                        # Check file size if max_file_size is specified
                        if (
                            max_file_size is None
                            or len(content.encode("utf-8")) <= max_file_size
                        ):
                            files[current_file] = content
                            if verbose:
                                pbar.write(
                                    f"Added file: {current_file} ({len(content.encode('utf-8'))} bytes)"
                                )
                        else:
                            if verbose:
                                pbar.write(
                                    f"Skipping file due to size limit: {current_file}"
                                )

                        content_lines = []

                    # Extract the new file path
                    current_file = line.strip("# \n")
                    if verbose:
                        pbar.write(f"Found file in gitin output: {current_file}")

                # Check for code block markers
                elif line.strip() == "```" or line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    # Skip the code block markers
                    continue

                # If we're in a code block and have a current file, collect the content
                elif in_code_block and current_file:
                    content_lines.append(line)

        # Don't forget the last file
        if current_file and content_lines:
            content = "".join(content_lines)

            # Check file size if max_file_size is specified
            if max_file_size is None or len(content.encode("utf-8")) <= max_file_size:
                files[current_file] = content
                if verbose:
                    print(
                        f"Added file: {current_file} ({len(content.encode('utf-8'))} bytes)"
                    )
            else:
                if verbose:
                    print(f"Skipping file due to size limit: {current_file}")

        return files
