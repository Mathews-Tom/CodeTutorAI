"""
CodeTutorAI - Mock Test

This module provides a test script for CodeTutorAI using mock data.
"""

import argparse
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv

from codetutorai.flow import create_tutorial_flow
from codetutorai.utils.mock_data import create_mock_data


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Test CodeTutorAI with mock data")

    parser.add_argument(
        "--output-dir",
        default="mock_output",
        help="Output directory for the tutorial (default: mock_output)",
    )

    parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic", "palm"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )

    parser.add_argument(
        "--api-key",
        help="API key for the LLM provider (defaults to environment variable)",
    )

    parser.add_argument(
        "--max-chunk-size",
        type=int,
        default=5000,
        help="Maximum chunk size in characters for LLM analysis (default: 5000)",
    )

    parser.add_argument(
        "--ordering-method",
        choices=["auto", "topological", "learning_curve", "llm"],
        default="auto",
        help="Method to use for chapter ordering (default: auto)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of chapters to generate in parallel (default: 1)",
    )

    parser.add_argument(
        "--output-formats",
        default="markdown",
        help="Comma-separated list of output formats: markdown,html,pdf,github_pages (default: markdown)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the test script.

    Returns:
        int: Exit code
    """
    # Load environment variables from .env file
    load_dotenv()

    # Parse command line arguments
    args = parse_args()

    # Create the output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Create mock data
    mock_data = create_mock_data()

    # Create the context dictionary
    context: Dict[str, Any] = {
        "repo_url": "https://github.com/mock/repo",
        "output_dir": args.output_dir,
        "llm_provider": args.llm_provider,
        "api_key": args.api_key,
        "max_chunk_size": args.max_chunk_size,
        "batch_size": args.batch_size,
        "output_formats": args.output_formats.split(","),
        "include_patterns": ["*"],
        "exclude_patterns": [],
        "fetch_repo_metadata": False,
        "verbose": args.verbose,
    }

    # Add mock data to the context
    context.update(mock_data)

    # Create the tutorial flow
    flow = create_tutorial_flow()

    try:
        # Run the flow
        flow.run(context)

        print(f"Tutorial generated successfully in {args.output_dir}")
        print(f"Main index file: {os.path.join(args.output_dir, 'index.md')}")
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
