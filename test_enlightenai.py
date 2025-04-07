#!/usr/bin/env python3
"""
Test script for EnlightenAI.

This script tests the EnlightenAI tutorial generation workflow with a sample GitHub repository.
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from flow import create_tutorial_flow

# Load environment variables from .env file
load_dotenv()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test EnlightenAI with a sample GitHub repository"
    )

    parser.add_argument(
        "--repo-url",
        default="https://github.com/Mathews-Tom/EnlightenAI",
        help="GitHub repository URL (default: this repository)",
    )

    parser.add_argument(
        "--web-url",
        default="https://docs.crawl4ai.com/",
        help="Web page URL to crawl for additional context (default: crawl4ai docs)",
    )

    parser.add_argument(
        "--output-dir",
        default="test_output",
        help="Output directory for generated tutorial (default: test_output/)",
    )

    parser.add_argument(
        "--include",
        default="*.py",
        help="Comma-separated list of file patterns to include (default: *.py)",
    )

    parser.add_argument(
        "--exclude",
        default="test_*,*__pycache__*",
        help="Comma-separated list of file patterns to exclude (default: test_*,*__pycache__*)",
    )

    parser.add_argument(
        "--llm-provider",
        default="openai",
        choices=["openai", "anthropic", "palm", "local"],
        help="LLM provider to use (default: openai)",
    )

    parser.add_argument(
        "--api-key",
        help="API key for the LLM provider (defaults to environment variable)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def main():
    """Main entry point for the test script."""
    args = parse_arguments()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Create shared context for the workflow
    context = {
        "repo_url": args.repo_url,
        "web_url": args.web_url,
        "output_dir": args.output_dir,
        "include_patterns": args.include.split(","),
        "exclude_patterns": args.exclude.split(","),
        "llm_provider": args.llm_provider,
        "api_key": args.api_key,
        "verbose": args.verbose,
        "files": {},  # Will store {path: content} pairs
        "web_content": {},  # Will store web crawl results
        "abstractions": [],  # Will store identified components
        "relationships": [],  # Will store component relationships
        "chapter_order": [],  # Will store ordered chapter sequence
    }

    # Create and run the tutorial generation flow
    try:
        flow = create_tutorial_flow()
        result = flow.run(context)

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
