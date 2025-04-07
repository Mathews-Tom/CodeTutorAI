"""
EnlightenAI - Test Script

This module provides a test script for EnlightenAI using real data.
"""

import argparse
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv

from enlightenai.flow import create_tutorial_flow


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Test EnlightenAI with real data")

    parser.add_argument("repo_url", help="URL of the GitHub repository to analyze")

    parser.add_argument(
        "--output-dir",
        default="tutorial_output",
        help="Output directory for the tutorial (default: tutorial_output)",
    )

    parser.add_argument(
        "--web-url",
        help="URL of a website with additional information about the repository",
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
        "--max-file-size",
        type=int,
        default=1048576,  # 1MB
        help="Maximum file size in bytes to include (default: 1MB)",
    )

    parser.add_argument(
        "--max-files",
        type=int,
        default=100,
        help="Maximum number of files to include (default: 100)",
    )

    parser.add_argument(
        "--include-patterns",
        help="Comma-separated list of file patterns to include (e.g., '*.py,*.js')",
    )

    parser.add_argument(
        "--exclude-patterns",
        help="Comma-separated list of file patterns to exclude (e.g., '*.md,*.txt')",
    )

    parser.add_argument(
        "--fetch-repo-metadata",
        action="store_true",
        help="Fetch repository metadata (stars, forks, etc.)",
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

    # Create the context dictionary
    context: Dict[str, Any] = {
        "repo_url": args.repo_url,
        "output_dir": args.output_dir,
        "web_url": args.web_url,
        "llm_provider": args.llm_provider,
        "api_key": args.api_key,
        "max_file_size": args.max_file_size,
        "max_files": args.max_files,
        "include_patterns": args.include_patterns.split(",")
        if args.include_patterns
        else None,
        "exclude_patterns": args.exclude_patterns.split(",")
        if args.exclude_patterns
        else None,
        "max_chunk_size": args.max_chunk_size,
        "batch_size": args.batch_size,
        "output_formats": args.output_formats.split(","),
        "ordering_method": args.ordering_method,
        "fetch_repo_metadata": args.fetch_repo_metadata,
        "verbose": args.verbose,
    }

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
