"""
CodeTutorAI - Identify Abstractions Node

This module contains the IdentifyAbstractionsNode class for identifying key abstractions
in a codebase.
"""

import json
import os
import re
from typing import Any, Dict, List, Set, Tuple

from tqdm import tqdm

from codetutorai.nodes.node import Node
from codetutorai.utils.llm_client import LLMClient  # Import the client class


class IdentifyAbstractionsNode(Node):
    """Node for identifying key abstractions in a codebase."""

    def process(self, context):
        """Identify key abstractions in a codebase.
        
        Args:
            context (dict): The shared context dictionary containing:
                - file_paths: List of relative file paths in the repository
                - repo_dir: Local path to the cloned repository
                - repo_name: Name of the repository
                - repo_metadata: Repository metadata
                - web_content: Web content related to the repository
                - output_dir: Output directory for the tutorial
                - llm_provider: LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output
                - cache_enabled: Whether to enable LLM caching
                - cache_dir: Directory for the LLM cache

        Returns:
            dict: Dictionary containing the identified abstractions.
        """
        verbose = context.get("verbose", False)
        file_paths = context.get("file_paths", [])
        repo_name = context.get("repo_name", "")
        # repo_dir is needed if we decide to read file content here later
        repo_metadata = context.get("repo_metadata", {})
        web_content = context.get("web_content", {})
        output_dir = context.get("output_dir", "tutorial_output")
        llm_provider = context.get("llm_provider", "openai")
        api_key = context.get("api_key")
        cache_enabled = context.get("cache_enabled", False)
        cache_dir = context.get("cache_dir", ".llm_cache")

        if verbose:
            print(f"Identifying abstractions in {len(file_paths)} files...")
        
        # Group files by directory
        file_groups = self._group_files_by_directory(file_paths)
        
        if verbose:
            print(f"Grouped files into {len(file_groups)} directories")
        # Instantiate the LLM client with caching settings
        llm_client = LLMClient(
            provider=llm_provider,
            api_key=api_key,
            cache_enabled=cache_enabled,
            cache_dir=cache_dir,
            verbose=verbose # Pass verbose setting to client for cache logging
        )
        # Identify abstractions in each file group
        abstractions = []

        
        for group_name, group_file_paths in file_groups.items():
            if verbose:
                print(f"Identifying abstractions in {group_name}...")
            
            # Create a prompt for the LLM
            prompt = self._create_abstraction_prompt(group_name, group_file_paths, repo_name, repo_metadata, web_content)
            
            # Call the LLM using the client instance
            response = llm_client.call(
                prompt,
                # provider and api_key are handled by the client instance
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse the response
            group_abstractions = self._parse_abstraction_response(response, group_file_paths)
            
            # Add the abstractions to the list
            abstractions.extend(group_abstractions)
            
            if verbose:
                print(f"Found {len(group_abstractions)} abstractions in {group_name}")
        
        # Deduplicate abstractions
        abstractions = self._deduplicate_abstractions(abstractions)
        
        if verbose:
            print(f"Identified {len(abstractions)} unique abstractions")
        
        # Save the abstractions to a file
        abstractions_path = os.path.join(output_dir, "abstractions.json")
        with open(abstractions_path, "w", encoding="utf-8") as f:
            json.dump(abstractions, f, indent=2)
        
        if verbose:
            print(f"Saved abstractions to {abstractions_path}")
        
        # Update the context
        return {"abstractions": abstractions}
    
    def _group_files_by_directory(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """Group files by directory.

        Args:
            file_paths (list): List of relative file paths

        Returns:
            dict: Dictionary mapping directory names to lists of file paths
        """
        file_groups = {}
        
        for file_path in file_paths:
            # Get the directory path
            dir_path = os.path.dirname(file_path) or "" # Handle root files
            
            # Use the directory name as the group name
            if dir_path:
                group_name = os.path.basename(dir_path)
            else:
                group_name = "root"
            
            # Add the file to the group
            if group_name not in file_groups:
                file_groups[group_name] = []

            file_groups[group_name].append(file_path)
        
        return file_groups
    
    def _create_abstraction_prompt(
        self, 
        group_name: str,
        group_file_paths: List[str],
        repo_name: str,
        repo_metadata: Dict[str, Any],
        web_content: Dict[str, Dict[str, str]]
    ) -> str:
        """Create a prompt for the LLM to identify abstractions.

        Args:
            group_name (str): Name of the file group
            group_file_paths (list): List of file paths in this group
            repo_name (str): Name of the repository
            repo_metadata (dict): Repository metadata
            web_content (dict): Web content related to the repository

        Returns:
            str: The prompt for the LLM
        """
        # Create a summary of the files
        file_summary = "\n".join([f"- {file_path}" for file_path in group_file_paths])
        
        # Create a summary of the web content
        web_summary = ""
        if web_content:
            web_summary = "# Web Content\n"
            for url, page in list(web_content.items())[:3]:  # Limit to 3 pages
                web_summary += f"## {page.get('title', 'Untitled')}\n"
                web_summary += f"{page.get('content', '')[:500]}...\n\n"
        
        # Create the prompt
        prompt = f"""
You are an expert software architect analyzing a codebase to identify key abstractions.

# Repository Information
Name: {repo_name}
Description: {repo_metadata.get('description', '')}

# Files in the '{group_name}' Directory
{file_summary}

{web_summary}

# Task
Identify the key abstractions (components, modules, classes, concepts) in these files.
For each abstraction, provide:
1. A name
2. A brief description
3. A list of files that implement or relate to this abstraction

# Output Format
Return a JSON array of abstractions, where each abstraction is an object with the following properties:
- name: The name of the abstraction
- description: A brief description of the abstraction
- files: An array of file paths that implement or relate to this abstraction

Example:
```json
[
  {{
    "name": "UserAuthentication",
    "description": "Handles user authentication and authorization",
    "files": ["auth/login.py", "auth/session.py"]
  }},
  {{
    "name": "DataStorage",
    "description": "Manages data persistence and retrieval",
    "files": ["storage/database.py", "storage/cache.py"]
  }}
]
```

Focus on identifying meaningful abstractions that would be helpful for understanding the codebase.
"""
        
        return prompt
    
    def _parse_abstraction_response(self, response: str, group_file_paths: List[str]) -> List[Dict[str, Any]]:
        """Parse the LLM response to extract abstractions.

        Args:
            response (str): The LLM response
            group_file_paths (list): List of file paths in this group

        Returns:
            list: List of abstraction dictionaries
        """
        # Try to parse the response as JSON
        try:
            # Find the JSON array in the response
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                abstractions = json.loads(json_str)
                
                # Validate the abstractions
                valid_abstractions = []
                for abstraction in abstractions:
                    if isinstance(abstraction, dict) and "name" in abstraction and "description" in abstraction:
                        # Ensure files is a list
                        if "files" not in abstraction or not isinstance(abstraction["files"], list):
                            abstraction["files"] = []
                        
                        # Filter out files that don't exist in the group
                        abstraction["files"] = [file_path for file_path in abstraction["files"] if file_path in group_file_paths]
                        
                        valid_abstractions.append(abstraction)
                
                return valid_abstractions
        except Exception:
            pass
        
        # If JSON parsing fails, try to extract abstractions using regex
        abstractions = []
        
        # Look for abstraction names and descriptions
        name_pattern = r"(?:^|\n)#+\s+(.+?)(?:\n|$)"
        desc_pattern = r"(?:^|\n)(?:Description|About):\s+(.+?)(?:\n|$)"
        files_pattern = r"(?:^|\n)(?:Files|Implements):\s+(.+?)(?:\n|$)"
        
        for match in re.finditer(name_pattern, response, re.MULTILINE):
            name = match.group(1).strip()
            
            # Look for a description
            desc_match = re.search(desc_pattern, response[match.end():], re.MULTILINE)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Look for files
            files_match = re.search(files_pattern, response[match.end():], re.MULTILINE)
            files_str = files_match.group(1).strip() if files_match else ""
            files = [file.strip() for file in files_str.split(",")]
            
            # Filter out files that don't exist in the group
            files = [file_path for file_path in files if file_path in group_file_paths]
            
            # Add the abstraction
            abstractions.append({
                "name": name,
                "description": description,
                "files": files
            })
        
        return abstractions
    
    def _deduplicate_abstractions(self, abstractions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate abstractions by merging similar ones.
        
        Args:
            abstractions (list): List of abstraction dictionaries
            
        Returns:
            list: List of deduplicated abstraction dictionaries
        """
        # Create a mapping of abstraction names to indices
        name_to_index = {}
        for i, abstraction in enumerate(abstractions):
            name = abstraction["name"].lower()
            if name in name_to_index:
                # Merge the abstractions
                existing_idx = name_to_index[name]
                existing = abstractions[existing_idx]
                
                # Merge the descriptions
                if len(abstraction["description"]) > len(existing["description"]):
                    existing["description"] = abstraction["description"]
                
                # Merge the files
                existing["files"] = list(set(existing["files"] + abstraction["files"]))
            else:
                name_to_index[name] = i
        
        # Create a new list with the deduplicated abstractions
        deduplicated = []
        for i, abstraction in enumerate(abstractions):
            name = abstraction["name"].lower()
            if name_to_index[name] == i:
                deduplicated.append(abstraction)
        
        return deduplicated
