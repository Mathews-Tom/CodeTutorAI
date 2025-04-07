"""
EnlightenAI - Identify Abstractions Node

This module contains the IdentifyAbstractionsNode class, which is responsible for
identifying key abstractions (components, classes, modules) in the codebase.
"""

import json
import re
from collections import defaultdict

from tqdm import tqdm

from nodes import Node
from utils.call_llm import call_llm
from utils.code_analysis import (
    analyze_codebase_structure,
    chunk_codebase,
    detect_language,
    extract_code_structure,
    group_files_by_language,
)


class IdentifyAbstractionsNode(Node):
    """Node for identifying key abstractions in the codebase."""

    def process(self, context):
        """Identify key abstractions in the codebase.

        Args:
            context (dict): The shared context dictionary containing:
                - files: Dictionary mapping file paths to file contents
                - web_content: Dictionary containing web crawl results
                - repo_metadata: Dictionary containing repository metadata
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - max_chunk_size: Maximum size of each chunk in characters
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the identified abstractions.
        """
        files = context["files"]
        web_content = context.get("web_content", {})
        repo_metadata = context.get("repo_metadata", {})
        max_chunk_size = context.get("max_chunk_size", 5000)
        verbose = context.get("verbose", False)

        if verbose:
            print(f"Identifying abstractions from {len(files)} files")
            if web_content:
                print(f"Including web content in analysis")
            if repo_metadata:
                print(f"Including repository metadata in analysis")

        # Analyze codebase structure
        with tqdm(
            total=len(files), desc="Analyzing codebase structure", disable=not verbose
        ) as pbar:
            codebase_structure = analyze_codebase_structure(files)
            pbar.update(len(files))

        # Group files by language
        language_groups = group_files_by_language(files)
        if verbose:
            print(f"Found {len(language_groups)} languages in the codebase:")
            for language, lang_files in language_groups.items():
                print(f"  - {language}: {len(lang_files)} files")

        # Chunk the codebase for analysis
        chunks = chunk_codebase(files, max_chunk_size)
        if verbose:
            print(f"Split codebase into {len(chunks)} chunks for analysis")

        # Process each chunk with the LLM
        all_abstractions = []
        with tqdm(
            total=len(chunks), desc="Processing chunks", disable=not verbose
        ) as pbar:
            for i, chunk in enumerate(chunks):
                # Prepare file summaries for the LLM prompt
                file_summaries = []
                for path, content in chunk.items():
                    file_summaries.append({"path": path, "content": content})

                # Add codebase structure summary
                structure_summary = self._create_structure_summary(codebase_structure)
                file_summaries.append(
                    {"path": "codebase_structure.json", "content": structure_summary}
                )

                # Add repository metadata if available
                if repo_metadata:
                    repo_summary = self._create_repo_summary(repo_metadata)
                    file_summaries.append(
                        {"path": "repo_metadata.json", "content": repo_summary}
                    )

                # Add web content if available and this is the first chunk
                if web_content and i == 0:
                    web_markdown = web_content.get("fit_markdown") or web_content.get(
                        "markdown", ""
                    )
                    if web_markdown:
                        # Limit web content length to avoid token limits
                        if len(web_markdown) > 10000:
                            web_markdown = web_markdown[:10000] + "... [truncated]"

                        file_summaries.append(
                            {"path": "web_content.md", "content": web_markdown}
                        )

                # Create the LLM prompt
                prompt = self._create_abstraction_prompt(
                    file_summaries, i + 1, len(chunks)
                )

                # Call the LLM to identify abstractions
                llm_response = call_llm(
                    prompt=prompt,
                    provider=context.get("llm_provider", "openai"),
                    api_key=context.get("api_key"),
                    max_tokens=2000,
                    temperature=0.2,
                )

                # Parse the LLM response to extract abstractions
                chunk_abstractions = self._parse_abstractions(llm_response)
                all_abstractions.extend(chunk_abstractions)
                pbar.update(1)

        # Deduplicate abstractions
        deduplicated_abstractions = self._deduplicate_abstractions(all_abstractions)

        if verbose:
            print(
                f"Identified {len(deduplicated_abstractions)} abstractions after deduplication"
            )
            for abstraction in deduplicated_abstractions:
                abstraction_type = abstraction.get("type", "N/A")
                print(f"  - {abstraction['name']}: {abstraction_type}")

        # Update the context with the identified abstractions
        context["abstractions"] = deduplicated_abstractions
        context["codebase_structure"] = codebase_structure

        # Return None as we've updated the context directly
        return None

    def _create_abstraction_prompt(self, file_summaries, chunk_num=1, total_chunks=1):
        """Create a prompt for the LLM to identify abstractions.

        Args:
            file_summaries (list): List of dictionaries containing file paths and contents
            chunk_num (int): Current chunk number (1-based)
            total_chunks (int): Total number of chunks

        Returns:
            str: The prompt for the LLM
        """
        prompt = f"""
        You are an expert code analyzer. Your task is to identify key abstractions (components, classes, modules) in the following codebase.

        This is chunk {chunk_num} of {total_chunks} from the codebase.

        For each abstraction, provide:
        1. A unique name
        2. The type of abstraction (e.g., class, module, function, interface)
        3. A brief description of its purpose
        4. The file(s) where it is defined or implemented
        5. Key responsibilities or features

        Format your response as a JSON array of objects with the following structure:
        [
            {{
                "name": "AbstractionName",
                "type": "class|module|function|interface",
                "description": "Brief description of the abstraction",
                "files": ["path/to/file1.py", "path/to/file2.py"],
                "responsibilities": ["Responsibility 1", "Responsibility 2"]
            }},
            ...
        ]

        Focus on the most important abstractions that would help someone understand the overall architecture of the codebase.
        Be precise and specific in your descriptions.
        Identify abstractions at different levels of granularity (high-level components, specific classes, etc.).

        Here are the files in this chunk of the codebase:
        """

        for file_summary in file_summaries:
            prompt += f"\n--- {file_summary['path']} ---\n"
            prompt += file_summary["content"]
            prompt += "\n\n"

        prompt += "\nJSON response:"

        return prompt

    def _create_structure_summary(self, codebase_structure):
        """Create a summary of the codebase structure for the LLM.

        Args:
            codebase_structure (dict): Dictionary containing the analyzed structure

        Returns:
            str: JSON string summarizing the codebase structure
        """
        # Create a simplified version of the structure to avoid token limits
        summary = {
            "languages": codebase_structure.get("languages", {}),
            "file_count": sum(codebase_structure.get("languages", {}).values()),
            "abstraction_counts": {
                "classes": len(
                    codebase_structure.get("abstractions", {}).get("classes", [])
                ),
                "functions": len(
                    codebase_structure.get("abstractions", {}).get("functions", [])
                ),
                "interfaces": len(
                    codebase_structure.get("abstractions", {}).get("interfaces", [])
                ),
                "structs": len(
                    codebase_structure.get("abstractions", {}).get("structs", [])
                ),
            },
        }

        return json.dumps(summary, indent=2)

    def _create_repo_summary(self, repo_metadata):
        """Create a summary of the repository metadata for the LLM.

        Args:
            repo_metadata (dict): Dictionary containing repository metadata

        Returns:
            str: JSON string summarizing the repository metadata
        """
        # Create a simplified version of the metadata to avoid token limits
        summary = {
            "name": repo_metadata.get("full_name", ""),
            "description": repo_metadata.get("description", ""),
            "stars": repo_metadata.get("stargazers_count", 0),
            "forks": repo_metadata.get("forks_count", 0),
            "language": repo_metadata.get("language", ""),
            "topics": repo_metadata.get("topics", []),
        }

        return json.dumps(summary, indent=2)

    def _parse_abstractions(self, llm_response):
        """Parse the LLM response to extract abstractions.

        Args:
            llm_response (str): The LLM response containing JSON data

        Returns:
            list: List of abstraction dictionaries
        """
        # Extract JSON from the response (the LLM might include explanatory text)
        json_start = llm_response.find("[")
        json_end = llm_response.rfind("]") + 1

        if json_start == -1 or json_end == 0:
            # Try to find JSON in a code block
            code_block_pattern = r"```(?:json)?\s*\n(.+?)\n```"
            code_block_match = re.search(code_block_pattern, llm_response, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1).strip()
            else:
                raise ValueError("Failed to extract JSON from LLM response")
        else:
            json_str = llm_response[json_start:json_end]

        try:
            abstractions = json.loads(json_str)

            # Validate and clean up abstractions
            validated_abstractions = []
            for abstraction in abstractions:
                # Ensure required fields are present
                if "name" not in abstraction:
                    continue

                # Add default values for missing fields
                if "type" not in abstraction:
                    abstraction["type"] = "unknown"
                if "description" not in abstraction:
                    abstraction["description"] = ""
                if "files" not in abstraction:
                    abstraction["files"] = []
                if "responsibilities" not in abstraction:
                    abstraction["responsibilities"] = []

                validated_abstractions.append(abstraction)

            return validated_abstractions
        except json.JSONDecodeError as e:
            # Try to fix common JSON errors
            fixed_json_str = self._fix_json_errors(json_str)
            try:
                abstractions = json.loads(fixed_json_str)
                return abstractions
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")

    def _fix_json_errors(self, json_str):
        """Fix common JSON errors in LLM responses.

        Args:
            json_str (str): JSON string with potential errors

        Returns:
            str: Fixed JSON string
        """
        # Replace single quotes with double quotes
        json_str = re.sub(r"'([^']*)'\s*:", r'"\1":', json_str)

        # Fix trailing commas in arrays
        json_str = re.sub(r",\s*]}", r"]}", json_str)
        json_str = re.sub(r",\s*]", r"]", json_str)

        # Fix trailing commas in objects
        json_str = re.sub(r",\s*}", r"}", json_str)

        # Fix missing quotes around keys
        json_str = re.sub(r"([{,])\s*([a-zA-Z0-9_]+)\s*:", r'\1"\2":', json_str)

        return json_str

    def _deduplicate_abstractions(self, abstractions):
        """Deduplicate abstractions based on name similarity.

        Args:
            abstractions (list): List of abstraction dictionaries

        Returns:
            list: Deduplicated list of abstraction dictionaries
        """
        if not abstractions:
            return []

        # Group abstractions by name similarity
        name_groups = defaultdict(list)
        for abstraction in abstractions:
            name = abstraction["name"].lower()
            # Remove common prefixes/suffixes for comparison
            clean_name = re.sub(r"^(class|interface|struct|enum|type)\s+", "", name)
            clean_name = re.sub(r"(class|interface|struct|enum|type)$", "", clean_name)
            clean_name = clean_name.strip()
            name_groups[clean_name].append(abstraction)

        # Merge abstractions in each group
        deduplicated = []
        for name, group in name_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Merge abstractions with the same name
                merged = self._merge_abstractions(group)
                deduplicated.append(merged)

        return deduplicated

    def _merge_abstractions(self, abstractions):
        """Merge multiple abstractions into one.

        Args:
            abstractions (list): List of abstraction dictionaries to merge

        Returns:
            dict: Merged abstraction dictionary
        """
        if not abstractions:
            return {}

        # Use the first abstraction as a base
        merged = dict(abstractions[0])

        # Merge fields from other abstractions
        for abstraction in abstractions[1:]:
            # Use the most common type
            if "type" in abstraction and abstraction["type"] != merged.get("type"):
                merged["type"] = abstraction["type"]

            # Combine descriptions
            if "description" in abstraction and abstraction["description"]:
                if merged.get("description"):
                    merged["description"] += " " + abstraction["description"]
                else:
                    merged["description"] = abstraction["description"]

            # Combine files
            if "files" in abstraction:
                merged_files = set(merged.get("files", []))
                merged_files.update(abstraction["files"])
                merged["files"] = list(merged_files)

            # Combine responsibilities
            if "responsibilities" in abstraction:
                merged_resp = set(merged.get("responsibilities", []))
                merged_resp.update(abstraction["responsibilities"])
                merged["responsibilities"] = list(merged_resp)

        return merged
