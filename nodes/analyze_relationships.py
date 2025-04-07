"""
EnlightenAI - Analyze Relationships Node

This module contains the AnalyzeRelationshipsNode class, which is responsible for
analyzing relationships between abstractions in the codebase.
"""

import json
import re
from collections import defaultdict

from tqdm import tqdm

from nodes import Node
from utils.call_llm import call_llm
from utils.code_analysis import detect_language, extract_code_structure


class AnalyzeRelationshipsNode(Node):
    """Node for analyzing relationships between abstractions in the codebase."""

    def process(self, context):
        """Analyze relationships between abstractions in the codebase.

        Args:
            context (dict): The shared context dictionary containing:
                - files: Dictionary mapping file paths to file contents
                - web_content: Dictionary containing web crawl results
                - repo_metadata: Dictionary containing repository metadata
                - abstractions: List of abstraction dictionaries
                - codebase_structure: Dictionary containing analyzed codebase structure
                - llm_provider: The LLM provider to use
                - api_key: API key for the LLM provider
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the identified relationships.
        """
        files = context["files"]
        web_content = context.get("web_content", {})
        repo_metadata = context.get("repo_metadata", {})
        abstractions = context["abstractions"]
        codebase_structure = context.get("codebase_structure", {})
        verbose = context.get("verbose", False)

        if verbose:
            print(f"Analyzing relationships between {len(abstractions)} abstractions")
            if web_content:
                print(f"Including web content in relationship analysis")
            if repo_metadata:
                print(f"Including repository metadata in relationship analysis")

        # Skip if no abstractions were identified
        if not abstractions:
            if verbose:
                print("No abstractions to analyze. Skipping relationship analysis.")
            context["relationships"] = []
            context["relationship_graph"] = {}
            context["mermaid_diagram"] = ""
            return None

        # Add web content to files if available
        files_with_web = dict(files)
        web_markdown = web_content.get("fit_markdown") or web_content.get(
            "markdown", ""
        )
        if web_markdown:
            files_with_web["web_content.md"] = web_markdown

        # Process abstractions in batches to avoid token limits
        all_relationships = []
        batch_size = min(
            10, len(abstractions)
        )  # Process up to 10 abstractions at a time
        num_batches = (len(abstractions) + batch_size - 1) // batch_size

        with tqdm(
            total=num_batches, desc="Analyzing relationships", disable=not verbose
        ) as pbar:
            for i in range(0, len(abstractions), batch_size):
                batch_abstractions = abstractions[i : i + batch_size]

                # Create the LLM prompt for this batch
                prompt = self._create_relationship_prompt(
                    batch_abstractions,
                    files_with_web,
                    codebase_structure,
                    i // batch_size + 1,
                    num_batches,
                )

                # Call the LLM to analyze relationships
                llm_response = call_llm(
                    prompt=prompt,
                    provider=context.get("llm_provider", "openai"),
                    api_key=context.get("api_key"),
                    max_tokens=2000,
                    temperature=0.2,
                )

                # Parse the LLM response to extract relationships
                batch_relationships = self._parse_relationships(llm_response)
                all_relationships.extend(batch_relationships)

                pbar.update(1)

        # Validate and deduplicate relationships
        validated_relationships = self._validate_relationships(
            all_relationships, abstractions
        )

        if verbose:
            print(
                f"Identified {len(validated_relationships)} relationships after validation"
            )
            for relationship in validated_relationships:
                source = relationship.get("source", "Unknown")
                rel_type = relationship.get("type", "relates to")
                target = relationship.get("target", "Unknown")
                print(f"  - {source} {rel_type} {target}")

        # Generate relationship graph
        relationship_graph = self._generate_relationship_graph(validated_relationships)

        # Generate Mermaid diagram
        mermaid_diagram = self._generate_mermaid_diagram(
            validated_relationships, abstractions
        )

        # Update the context with the identified relationships
        context["relationships"] = validated_relationships
        context["relationship_graph"] = relationship_graph
        context["mermaid_diagram"] = mermaid_diagram

        # Return None as we've updated the context directly
        return None

    def _create_relationship_prompt(
        self, abstractions, files, codebase_structure=None, batch_num=1, total_batches=1
    ):
        """Create a prompt for the LLM to analyze relationships.

        Args:
            abstractions (list): List of abstraction dictionaries
            files (dict): Dictionary mapping file paths to file contents
            codebase_structure (dict, optional): Dictionary containing analyzed codebase structure
            batch_num (int): Current batch number (1-based)
            total_batches (int): Total number of batches

        Returns:
            str: The prompt for the LLM
        """
        prompt = f"""
        You are an expert code analyzer. Your task is to identify relationships between the key abstractions in the codebase.

        This is batch {batch_num} of {total_batches} of abstractions to analyze.

        For each relationship, provide:
        1. The source abstraction name
        2. The target abstraction name
        3. The type of relationship (choose the most specific one that applies):
           - inherits: Inheritance relationship (e.g., class extends another class)
           - implements: Implementation relationship (e.g., class implements an interface)
           - composes: Composition relationship (e.g., class has an instance of another class)
           - aggregates: Aggregation relationship (e.g., class has a collection of another class)
           - uses: Usage relationship (e.g., class calls methods of another class)
           - depends: Dependency relationship (e.g., class depends on another class)
           - creates: Creation relationship (e.g., class creates instances of another class)
           - calls: Method call relationship (e.g., method calls another method)
           - imports: Import relationship (e.g., file imports another file)
        4. A brief description of the relationship

        Format your response as a JSON array of objects with the following structure:
        [
            {{
                "source": "SourceAbstractionName",
                "target": "TargetAbstractionName",
                "type": "inherits|implements|composes|aggregates|uses|depends|creates|calls|imports",
                "description": "Brief description of the relationship"
            }},
            ...
        ]

        Be precise and specific in your analysis. Focus on direct relationships that are evident in the code.
        Only include relationships between abstractions in the provided list.
        """

        # Add codebase structure summary if available
        if codebase_structure:
            prompt += "\n\nCodebase Structure Summary:\n"
            prompt += json.dumps(
                {
                    "languages": codebase_structure.get("languages", {}),
                    "file_count": sum(codebase_structure.get("languages", {}).values()),
                    "abstraction_counts": {
                        "classes": len(
                            codebase_structure.get("abstractions", {}).get(
                                "classes", []
                            )
                        ),
                        "functions": len(
                            codebase_structure.get("abstractions", {}).get(
                                "functions", []
                            )
                        ),
                        "interfaces": len(
                            codebase_structure.get("abstractions", {}).get(
                                "interfaces", []
                            )
                        ),
                        "structs": len(
                            codebase_structure.get("abstractions", {}).get(
                                "structs", []
                            )
                        ),
                    },
                },
                indent=2,
            )

        # Add abstractions to the prompt
        prompt += "\n\nHere are the abstractions to analyze in this batch:\n"
        prompt += json.dumps(abstractions, indent=2)

        # Add relevant file contents
        prompt += "\n\nHere are the relevant files:\n\n"

        # Get the files referenced by the abstractions
        relevant_files = set()
        for abstraction in abstractions:
            for file_path in abstraction.get("files", []):
                relevant_files.add(file_path)

        # Add the relevant file contents to the prompt
        for file_path in relevant_files:
            if file_path in files:
                content = files[file_path]
                # Limit content length to avoid token limits
                if len(content) > 3000:
                    content = content[:3000] + "... [truncated]"

                prompt += f"\n--- {file_path} ---\n"
                prompt += content
                prompt += "\n\n"

        prompt += "\nJSON response:"

        return prompt

    def _parse_relationships(self, llm_response):
        """Parse the LLM response to extract relationships.

        Args:
            llm_response (str): The LLM response containing JSON data

        Returns:
            list: List of relationship dictionaries
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
                # Return empty list if no JSON found
                return []
        else:
            json_str = llm_response[json_start:json_end]

        try:
            relationships = json.loads(json_str)

            # Validate and clean up relationships
            validated_relationships = []
            for relationship in relationships:
                # Ensure required fields are present
                if "source" not in relationship or "target" not in relationship:
                    continue

                # Add default values for missing fields
                if "type" not in relationship:
                    relationship["type"] = "relates to"
                if "description" not in relationship:
                    relationship["description"] = ""

                validated_relationships.append(relationship)

            return validated_relationships
        except json.JSONDecodeError:
            # Try to fix common JSON errors
            fixed_json_str = self._fix_json_errors(json_str)
            try:
                relationships = json.loads(fixed_json_str)
                return relationships
            except json.JSONDecodeError:
                # Return empty list if JSON parsing fails
                return []

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
        
    def _validate_relationships(self, relationships, abstractions):
        """Validate and deduplicate relationships.
        
        Args:
            relationships (list): List of relationship dictionaries
            abstractions (list): List of abstraction dictionaries
            
        Returns:
            list: Validated and deduplicated list of relationship dictionaries
        """
        if not relationships:
            return []
        
        # Create a set of abstraction names for validation
        abstraction_names = {abstraction["name"] for abstraction in abstractions}
        
        # Validate relationships
        valid_relationships = []
        for relationship in relationships:
            source = relationship.get("source")
            target = relationship.get("target")
            
            # Skip if source or target is missing
            if not source or not target:
                continue
                
            # Skip self-relationships
            if source == target:
                continue
                
            # Skip if source or target is not in the list of abstractions
            if source not in abstraction_names or target not in abstraction_names:
                continue
                
            # Add to valid relationships
            valid_relationships.append(relationship)
        
        # Deduplicate relationships
        deduplicated = []
        relationship_keys = set()
        
        for relationship in valid_relationships:
            key = (relationship["source"], relationship["type"], relationship["target"])
            if key not in relationship_keys:
                relationship_keys.add(key)
                deduplicated.append(relationship)
        
        return deduplicated
    
    def _generate_relationship_graph(self, relationships):
        """Generate a relationship graph from the relationships.
        
        Args:
            relationships (list): List of relationship dictionaries
            
        Returns:
            dict: Dictionary representing the relationship graph
        """
        graph = defaultdict(list)
        
        for relationship in relationships:
            source = relationship["source"]
            target = relationship["target"]
            rel_type = relationship["type"]
            description = relationship.get("description", "")
            
            # Add to graph
            graph[source].append({
                "target": target,
                "type": rel_type,
                "description": description
            })
        
        return dict(graph)
    
    def _generate_mermaid_diagram(self, relationships, abstractions):
        """Generate a Mermaid diagram from the relationships.
        
        Args:
            relationships (list): List of relationship dictionaries
            abstractions (list): List of abstraction dictionaries
            
        Returns:
            str: Mermaid diagram code
        """
        # Create a mapping of abstraction names to types
        abstraction_types = {}
        for abstraction in abstractions:
            abstraction_types[abstraction["name"]] = abstraction.get("type", "unknown")
        
        # Start the Mermaid diagram
        mermaid = "```mermaid\nflowchart TD\n"
        
        # Add nodes
        for name, type_name in abstraction_types.items():
            # Clean the name for Mermaid compatibility
            clean_name = re.sub(r'[^a-zA-Z0-9]', '_', name)
            
            # Add node with shape based on type
            if type_name == "class":
                mermaid += f"    {clean_name}[\"<b>{name}</b><br><i>Class</i>\"]\n"
            elif type_name == "interface":
                mermaid += f"    {clean_name}[\"<b>{name}</b><br><i>Interface</i>\"]\n"
            elif type_name == "function":
                mermaid += f"    {clean_name}[\"<b>{name}</b><br><i>Function</i>\"]\n"
            elif type_name == "module":
                mermaid += f"    {clean_name}[\"<b>{name}</b><br><i>Module</i>\"]\n"
            else:
                mermaid += f"    {clean_name}[\"<b>{name}</b>\"]\n"
        
        # Add relationships
        for relationship in relationships:
            source = relationship["source"]
            target = relationship["target"]
            rel_type = relationship["type"]
            
            # Clean names for Mermaid compatibility
            clean_source = re.sub(r'[^a-zA-Z0-9]', '_', source)
            clean_target = re.sub(r'[^a-zA-Z0-9]', '_', target)
            
            # Add edge with style based on relationship type
            if rel_type == "inherits":
                mermaid += f"    {clean_source} -.-> {clean_target}\n"
            elif rel_type == "implements":
                mermaid += f"    {clean_source} -.-> {clean_target}\n"
            elif rel_type == "composes":
                mermaid += f"    {clean_source} --o {clean_target}\n"
            elif rel_type == "aggregates":
                mermaid += f"    {clean_source} --* {clean_target}\n"
            elif rel_type == "uses":
                mermaid += f"    {clean_source} --> {clean_target}\n"
            elif rel_type == "depends":
                mermaid += f"    {clean_source} --> {clean_target}\n"
            elif rel_type == "creates":
                mermaid += f"    {clean_source} ===> {clean_target}\n"
            elif rel_type == "calls":
                mermaid += f"    {clean_source} --> {clean_target}\n"
            elif rel_type == "imports":
                mermaid += f"    {clean_source} -.-> {clean_target}\n"
            else:
                mermaid += f"    {clean_source} --- {clean_target}\n"
        
        # End the Mermaid diagram
        mermaid += "```"
        
        return mermaid
