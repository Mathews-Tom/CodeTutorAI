"""
EnlightenAI - Mock Data for Testing

This module provides mock data for testing the EnlightenAI workflow without
making actual API calls or network requests.
"""

import os
import json
from typing import Dict, Any, Optional


class MockGitHubRepo:
    """Mock GitHub repository for testing."""
    
    def __init__(self, repo_name: str = "mock-repo"):
        """Initialize a mock GitHub repository.
        
        Args:
            repo_name (str, optional): Name of the mock repository
        """
        self.repo_name = repo_name
        self.files = self._create_mock_files()
    
    def _create_mock_files(self) -> Dict[str, str]:
        """Create mock files for the repository.
        
        Returns:
            dict: Dictionary mapping file paths to file contents
        """
        return {
            "main.py": """#!/usr/bin/env python3
\"\"\"
Mock Repository - Main Module

This is the main entry point for the mock repository.
\"\"\"

import sys
from core.processor import DataProcessor
from utils.helpers import format_output


def main():
    \"\"\"Main entry point for the application.\"\"\"
    processor = DataProcessor()
    data = processor.process_data()
    formatted_data = format_output(data)
    print(formatted_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
""",
            "core/processor.py": """\"\"\"
Mock Repository - Data Processor

This module contains the DataProcessor class for processing data.
\"\"\"

from models.data_model import DataModel
from utils.helpers import validate_data


class DataProcessor:
    \"\"\"Process data using the DataModel.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize a new DataProcessor.\"\"\"
        self.model = DataModel()
    
    def process_data(self):
        \"\"\"Process data using the model.
        
        Returns:
            dict: Processed data
        \"\"\"
        raw_data = self.model.get_data()
        if validate_data(raw_data):
            return self.model.transform_data(raw_data)
        else:
            raise ValueError("Invalid data")
""",
            "models/data_model.py": """\"\"\"
Mock Repository - Data Model

This module contains the DataModel class for data operations.
\"\"\"

class DataModel:
    \"\"\"Model for data operations.\"\"\"
    
    def get_data(self):
        \"\"\"Get raw data.
        
        Returns:
            dict: Raw data
        \"\"\"
        return {
            "id": 1,
            "name": "Example",
            "values": [10, 20, 30]
        }
    
    def transform_data(self, data):
        \"\"\"Transform raw data.
        
        Args:
            data (dict): Raw data
            
        Returns:
            dict: Transformed data
        \"\"\"
        return {
            "id": data["id"],
            "name": data["name"],
            "average": sum(data["values"]) / len(data["values"]),
            "total": sum(data["values"])
        }
""",
            "utils/helpers.py": """\"\"\"
Mock Repository - Helper Functions

This module contains helper functions for the application.
\"\"\"

def validate_data(data):
    \"\"\"Validate data structure.
    
    Args:
        data (dict): Data to validate
        
    Returns:
        bool: True if valid, False otherwise
    \"\"\"
    return (
        isinstance(data, dict) and
        "id" in data and
        "name" in data and
        "values" in data and
        isinstance(data["values"], list)
    )


def format_output(data):
    \"\"\"Format data for output.
    
    Args:
        data (dict): Data to format
        
    Returns:
        str: Formatted output
    \"\"\"
    return f\"ID: {data['id']}\\nName: {data['name']}\\nAverage: {data['average']}\\nTotal: {data['total']}\"
""",
            "tests/test_processor.py": """\"\"\"
Mock Repository - Tests for DataProcessor

This module contains tests for the DataProcessor class.
\"\"\"

import unittest
from core.processor import DataProcessor
from models.data_model import DataModel


class TestDataProcessor(unittest.TestCase):
    \"\"\"Tests for the DataProcessor class.\"\"\"
    
    def test_process_data(self):
        \"\"\"Test the process_data method.\"\"\"
        processor = DataProcessor()
        result = processor.process_data()
        
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Example")
        self.assertEqual(result["average"], 20.0)
        self.assertEqual(result["total"], 60)


if __name__ == "__main__":
    unittest.main()
""",
            "README.md": """# Mock Repository

This is a mock repository for testing the EnlightenAI tutorial generator.

## Structure

- `main.py`: Main entry point
- `core/`: Core functionality
- `models/`: Data models
- `utils/`: Utility functions
- `tests/`: Unit tests

## Usage

```python
python main.py
```
"""
        }
    
    def get_files(self) -> Dict[str, str]:
        """Get the mock files.
        
        Returns:
            dict: Dictionary mapping file paths to file contents
        """
        return self.files


class MockWebsite:
    """Mock website for testing."""
    
    def __init__(self, title: str = "Mock Website"):
        """Initialize a mock website.
        
        Args:
            title (str, optional): Title of the mock website
        """
        self.title = title
        self.content = self._create_mock_content()
    
    def _create_mock_content(self) -> Dict[str, str]:
        """Create mock content for the website.
        
        Returns:
            dict: Dictionary with website content
        """
        return {
            "title": self.title,
            "markdown": f"""# {self.title}

## Introduction

This is a mock website for testing the EnlightenAI tutorial generator.

## Features

- Feature 1: Lorem ipsum dolor sit amet
- Feature 2: Consectetur adipiscing elit
- Feature 3: Sed do eiusmod tempor incididunt

## Architecture

The system consists of the following components:

1. **DataProcessor**: Processes data using the DataModel
2. **DataModel**: Provides data operations
3. **Helper Functions**: Utility functions for validation and formatting

## Code Example

```python
def process_data():
    model = DataModel()
    raw_data = model.get_data()
    if validate_data(raw_data):
        return model.transform_data(raw_data)
    else:
        raise ValueError("Invalid data")
```

## Conclusion

This mock website demonstrates the structure and content of a typical documentation page.
""",
            "html": f"""<!DOCTYPE html>
<html>
<head>
    <title>{self.title}</title>
</head>
<body>
    <h1>{self.title}</h1>
    
    <h2>Introduction</h2>
    <p>This is a mock website for testing the EnlightenAI tutorial generator.</p>
    
    <h2>Features</h2>
    <ul>
        <li>Feature 1: Lorem ipsum dolor sit amet</li>
        <li>Feature 2: Consectetur adipiscing elit</li>
        <li>Feature 3: Sed do eiusmod tempor incididunt</li>
    </ul>
    
    <h2>Architecture</h2>
    <p>The system consists of the following components:</p>
    <ol>
        <li><strong>DataProcessor</strong>: Processes data using the DataModel</li>
        <li><strong>DataModel</strong>: Provides data operations</li>
        <li><strong>Helper Functions</strong>: Utility functions for validation and formatting</li>
    </ol>
    
    <h2>Code Example</h2>
    <pre><code>def process_data():
    model = DataModel()
    raw_data = model.get_data()
    if validate_data(raw_data):
        return model.transform_data(raw_data)
    else:
        raise ValueError("Invalid data")
    </code></pre>
    
    <h2>Conclusion</h2>
    <p>This mock website demonstrates the structure and content of a typical documentation page.</p>
</body>
</html>
"""
        }
    
    def get_content(self) -> Dict[str, str]:
        """Get the mock content.
        
        Returns:
            dict: Dictionary with website content
        """
        return self.content


def create_mock_repo_node():
    """Create a mock FetchRepoNode that uses mock data.
    
    Returns:
        Node: A mock FetchRepoNode
    """
    from nodes import Node
    
    class MockFetchRepoNode(Node):
        """Mock node for fetching files from a GitHub repository."""
        
        def process(self, context):
            """Fetch mock files instead of actual repository files.
            
            Args:
                context (dict): The shared context dictionary
                
            Returns:
                None: The context is updated directly with the mock files.
            """
            verbose = context.get("verbose", False)
            mock_repo = MockGitHubRepo()
            
            if verbose:
                print(f"Using mock repository: {mock_repo.repo_name}")
            
            # Get mock files
            files = mock_repo.get_files()
            
            # Filter files based on include/exclude patterns
            include_patterns = context.get("include_patterns", ["*"])
            exclude_patterns = context.get("exclude_patterns", [])
            
            from fnmatch import fnmatch
            
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
                print(f"Fetched {len(filtered_files)} mock files")
            
            # Return None as we've updated the context directly
            return None
    
    return MockFetchRepoNode()


def create_mock_web_node():
    """Create a mock FetchWebNode that uses mock data.
    
    Returns:
        Node: A mock FetchWebNode
    """
    from nodes import Node
    
    class MockFetchWebNode(Node):
        """Mock node for fetching content from web pages."""
        
        def process(self, context):
            """Fetch mock web content instead of actual web content.
            
            Args:
                context (dict): The shared context dictionary
                
            Returns:
                None: The context is updated directly with the mock content.
            """
            verbose = context.get("verbose", False)
            mock_website = MockWebsite()
            
            if verbose:
                print(f"Using mock website: {mock_website.title}")
            
            # Get mock content
            content = mock_website.get_content()
            
            # Update the context with the mock content
            context["web_content"] = {
                "markdown": content["markdown"],
                "fit_markdown": content["markdown"],
                "html": content["html"],
                "cleaned_html": content["html"],
                "url": "https://example.com/mock",
                "metadata": {"title": content["title"]}
            }
            
            if verbose:
                print(f"Fetched mock web content")
            
            # Return None as we've updated the context directly
            return None
    
    return MockFetchWebNode()


def create_mock_tutorial_flow(use_mock_repo=True, use_mock_web=True):
    """Create a tutorial flow with mock nodes for testing.
    
    Args:
        use_mock_repo (bool, optional): Whether to use a mock repository node
        use_mock_web (bool, optional): Whether to use a mock web node
        
    Returns:
        Flow: A configured Flow object with mock nodes
    """
    from flow import Flow
    from nodes.identify_abstractions import IdentifyAbstractionsNode
    from nodes.analyze_relationships import AnalyzeRelationshipsNode
    from nodes.order_chapters import OrderChaptersNode
    from nodes.write_chapters import WriteChaptersNode
    from nodes.combine_tutorial import CombineTutorialNode
    from nodes.fetch_repo_gitin import FetchRepoGitinNode
    from nodes.fetch_web import FetchWebNode
    
    flow = Flow()
    
    # Add nodes in the order they should execute
    if use_mock_repo:
        flow.add_node(create_mock_repo_node())
    else:
        flow.add_node(FetchRepoGitinNode())
    
    if use_mock_web:
        flow.add_node(create_mock_web_node())
    else:
        flow.add_node(FetchWebNode())
    
    flow.add_node(IdentifyAbstractionsNode())
    flow.add_node(AnalyzeRelationshipsNode())
    flow.add_node(OrderChaptersNode())
    flow.add_node(WriteChaptersNode())
    flow.add_node(CombineTutorialNode())
    
    return flow
