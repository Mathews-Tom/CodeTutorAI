#!/usr/bin/env python3
"""
EnlightenAI - CLI entry point

This module provides the command-line interface for EnlightenAI, a tool that
transforms complex GitHub repositories into structured, beginner-friendly tutorials.
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
        description="EnlightenAI - Transform GitHub repositories into structured tutorials"
    )

    parser.add_argument(
        "repo_url",
        help="GitHub repository URL (e.g., https://github.com/username/repo)",
    )

    parser.add_argument(
        "--web-url", help="Web page URL to crawl for additional context"
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="docs",
        help="Output directory for generated tutorial (default: docs/)",
    )

    parser.add_argument(
        "--include",
        default="*.py,*.js,*.ts,*.go,*.java,*.rb,*.rs,*.c,*.cpp,*.h,*.hpp",
        help="Comma-separated list of file patterns to include (default: common code files)",
    )

    parser.add_argument(
        "--exclude",
        default="*test*,*__pycache__*,*.pyc,node_modules/*,*venv*,*env*,*build*,*dist*",
        help="Comma-separated list of file patterns to exclude (default: tests and build artifacts)",
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
        "--github-token",
        help="GitHub API token for authentication (defaults to environment variable GITHUB_API_KEY)",
    )

    parser.add_argument(
        "--max-file-size",
        type=int,
        default=1024 * 1024,  # 1MB
        help="Maximum file size in bytes to include (default: 1MB)",
    )

    parser.add_argument(
        "--fetch-repo-metadata",
        action="store_true",
        default=True,
        help="Fetch repository metadata (default: True)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def main():
    """Main entry point for EnlightenAI."""
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
        "github_token": args.github_token or os.environ.get("GITHUB_API_KEY"),
        "max_file_size": args.max_file_size,
        "fetch_repo_metadata": args.fetch_repo_metadata,
        "verbose": args.verbose,
        "files": {},  # Will store {path: content} pairs
        "web_content": {},  # Will store web crawl results
        "repo_metadata": {},  # Will store repository metadata
        "abstractions": [],  # Will store identified components
        "relationships": [],  # Will store component relationships
        "chapter_order": [],  # Will store ordered chapter sequence
    }

    # Create and run the tutorial generation flow
    try:
        flow = create_tutorial_flow()
        result = flow.run(context)

        if args.verbose:
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
