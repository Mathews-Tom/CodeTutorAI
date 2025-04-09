"""
CodeTutorAI - History and Metadata Management Utilities
"""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the validation function
from .formatting import is_valid_github_url

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_FILENAME = "generation_history.json"


def save_generation_metadata(metadata: Dict[str, Any], history_file_path: Path) -> None:
    """
    Loads existing generation history, appends new metadata, and saves it back.

    Args:
        metadata (Dict[str, Any]): Dictionary containing metadata for the current run.
                                    Should include keys like 'timestamp', 'repo_url',
                                    'output_path', and relevant config settings.
        history_file_path (Path): Path to the JSON file storing the history.
    """
    history: List[Dict[str, Any]] = []

    # Ensure timestamp is present
    if "timestamp" not in metadata:
        metadata["timestamp"] = datetime.datetime.now().isoformat()

    try:
        # Load existing history if the file exists
        if history_file_path.exists() and history_file_path.is_file():
            with open(history_file_path, "r") as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list):
                        logger.warning(
                            f"History file {history_file_path} does not contain a list. Resetting history."
                        )
                        history = []
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not decode JSON from {history_file_path}. Starting new history."
                    )
                    history = []
        else:
            logger.info(
                f"History file {history_file_path} not found. Creating new history."
            )

        # Append new metadata
        history.append(metadata)

        # Ensure the directory exists before writing
        history_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save updated history
        with open(history_file_path, "w") as f:
            json.dump(history, f, indent=4)  # Use indent for readability

        logger.info(f"Successfully saved generation metadata to {history_file_path}")

    except IOError as e:
        logger.error(f"Error saving generation metadata to {history_file_path}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving metadata: {e}")


# Potential future function:
# def load_generation_history(history_file_path: Path) -> List[Dict[str, Any]]:
#     """Loads the generation history from the specified file."""
#     # ... implementation ...
# --- History Loading Functions ---

def load_generation_history(history_file_path: Path) -> List[Dict[str, Any]]:
    """Loads the generation history list from the specified JSON file."""
    if history_file_path.exists() and history_file_path.is_file():
        try:
            with open(history_file_path, "r") as f:
                history = json.load(f)
                if isinstance(history, list):
                    return history
                else:
                    logger.warning(f"History file {history_file_path} does not contain a list. Returning empty history.")
                    return []
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from {history_file_path}. Returning empty history.")
            return []
        except IOError as e:
            logger.error(f"Error reading history file {history_file_path}: {e}")
            return []
    else:
        logger.info(f"History file {history_file_path} not found. Returning empty history.")
        return []


def load_github_url_history(history_file_path: Path) -> List[str]:
    """
    Loads generation history and extracts a list of unique, valid GitHub URLs.

    Args:
        history_file_path (Path): Path to the JSON file storing the history.

    Returns:
        List[str]: A list of unique, valid GitHub repository URLs found in the history.
    """
    history = load_generation_history(history_file_path)
    unique_urls = set()

    for entry in history:
        url = entry.get("repo_url")
        # Check if URL exists and is a valid GitHub URL format
        if url and isinstance(url, str) and is_valid_github_url(url):
            unique_urls.add(url)

    # Return sorted list for consistent ordering in UI
    return sorted(list(unique_urls))
