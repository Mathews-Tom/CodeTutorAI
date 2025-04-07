"""
EnlightenAI - Fetch Repository Node

This module contains the FetchRepoGitinNode class for fetching a GitHub repository.
"""

import fnmatch
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from enlightenai.nodes.node import Node


class FetchRepoGitinNode(Node):
    """Node for fetching a GitHub repository."""

    def process(self, context):
        """Fetch a GitHub repository and extract its contents.

        Args:
            context (dict): The shared context dictionary containing:
                - repo_url: URL of the GitHub repository
                - max_file_size: Maximum file size in bytes to include
                - max_files: Maximum number of files to include
                - include_patterns: List of file patterns to include
                - exclude_patterns: List of file patterns to exclude
                - output_dir: Output directory for the tutorial
                - verbose: Whether to print verbose output

        Returns:
            dict: Dictionary containing the repository contents.
        """
        verbose = context.get("verbose", False)
        repo_url = context.get("repo_url")
        max_file_size = context.get("max_file_size", 1048576)  # 1MB
        max_files = context.get("max_files", 100)
        include_patterns = context.get("include_patterns")
        exclude_patterns = context.get("exclude_patterns")
        output_dir = context.get("output_dir", "tutorial_output")

        if not repo_url:
            raise ValueError("Repository URL is required")

        if verbose:
            print(f"Fetching repository: {repo_url}")
            print(f"Max file size: {max_file_size} bytes")
            print(f"Max files: {max_files}")
            print(f"Include patterns: {include_patterns}")
            print(f"Exclude patterns: {exclude_patterns}")

        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Fetch the repository
        repo_name = self._get_repo_name(repo_url)
        repo_dir = os.path.join(output_dir, "repo")

        if verbose:
            print(f"Cloning repository to {repo_dir}...")

        # Clone the repository
        self._clone_repository(repo_url, repo_dir, verbose)

        if verbose:
            print("Repository cloned successfully")

        # Get the repository files
        files = self._get_repo_files(
            repo_dir,
            max_file_size,
            max_files,
            include_patterns,
            exclude_patterns,
            verbose,
        )

        if verbose:
            print(f"Found {len(files)} files in the repository")

        # Get the repository metadata
        metadata = self._get_repo_metadata(repo_url, repo_dir, verbose)

        # Update the context
        return {
            "repo_name": repo_name,
            "repo_dir": repo_dir,
            "files": files,
            "repo_metadata": metadata,
        }

    def _get_repo_name(self, repo_url: str) -> str:
        """Extract the repository name from the URL.

        Args:
            repo_url (str): URL of the GitHub repository

        Returns:
            str: Repository name
        """
        # Remove trailing .git if present
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]

        # Extract the repository name
        repo_name = repo_url.split("/")[-1]

        return repo_name

    def _clone_repository(self, repo_url: str, repo_dir: str, verbose: bool) -> None:
        """Clone a GitHub repository.

        Args:
            repo_url (str): URL of the GitHub repository
            repo_dir (str): Directory to clone the repository to
            verbose (bool): Whether to print verbose output
        """
        # Remove the directory if it already exists
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

        # Clone the repository
        try:
            cmd = ["git", "clone", repo_url, repo_dir]
            if not verbose:
                cmd.append("--quiet")

            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error cloning repository: {str(e)}")

    def _get_repo_files(
        self,
        repo_dir: str,
        max_file_size: int,
        max_files: int,
        include_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]],
        verbose: bool,
    ) -> Dict[str, str]:
        """Get the repository files.

        Args:
            repo_dir (str): Path to the repository directory
            max_file_size (int): Maximum file size in bytes to include
            max_files (int): Maximum number of files to include
            include_patterns (list): List of file patterns to include
            exclude_patterns (list): List of file patterns to exclude
            verbose (bool): Whether to print verbose output

        Returns:
            dict: Dictionary mapping file paths to file contents
        """
        files = {}
        file_count = 0

        # Walk through the repository directory
        for root, dirs, filenames in os.walk(repo_dir):
            # Skip .git directory
            if ".git" in dirs:
                dirs.remove(".git")

            # Process files
            for filename in filenames:
                # Check if we've reached the maximum number of files
                if file_count >= max_files:
                    break

                # Get the file path
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_dir)

                # Check if the file matches the include patterns
                if include_patterns and not self._matches_patterns(
                    rel_path, include_patterns
                ):
                    continue

                # Check if the file matches the exclude patterns
                if exclude_patterns and self._matches_patterns(
                    rel_path, exclude_patterns
                ):
                    continue

                # Check the file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > max_file_size:
                        if verbose:
                            print(f"Skipping {rel_path} (size: {file_size} bytes)")
                        continue
                except Exception as e:
                    if verbose:
                        print(f"Error getting file size for {rel_path}: {str(e)}")
                    continue

                # Read the file content
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Add the file to the dictionary
                    files[rel_path] = content
                    file_count += 1

                    if verbose and file_count % 10 == 0:
                        print(f"Processed {file_count} files...")
                except Exception as e:
                    if verbose:
                        print(f"Error reading {rel_path}: {str(e)}")
                    continue

        return files

    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if a file path matches any of the given patterns.

        Args:
            file_path (str): File path to check
            patterns (list): List of patterns to match against

        Returns:
            bool: True if the file path matches any of the patterns, False otherwise
        """
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _get_repo_metadata(
        self, repo_url: str, repo_dir: str, verbose: bool
    ) -> Dict[str, Any]:
        """Get the repository metadata.

        Args:
            repo_url (str): URL of the GitHub repository
            repo_dir (str): Path to the repository directory
            verbose (bool): Whether to print verbose output

        Returns:
            dict: Repository metadata
        """
        metadata = {
            "url": repo_url,
            "name": self._get_repo_name(repo_url),
            "description": "",
            "stars": 0,
            "forks": 0,
            "issues": 0,
            "last_commit": "",
            "created_at": "",
            "updated_at": "",
        }

        # Try to get additional metadata from the repository
        try:
            # Get the repository description from the README
            readme_path = os.path.join(repo_dir, "README.md")
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()

                # Extract the first paragraph as the description
                description = readme_content.split("\n\n")[0].strip()
                metadata["description"] = description

            # Get the last commit
            cmd = ["git", "-C", repo_dir, "log", "-1", "--format=%H %an %ad %s"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            last_commit = result.stdout.strip()

            if last_commit:
                parts = last_commit.split(" ", 3)
                if len(parts) >= 4:
                    metadata["last_commit"] = {
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    }
        except Exception as e:
            if verbose:
                print(f"Error getting repository metadata: {str(e)}")

        return metadata
