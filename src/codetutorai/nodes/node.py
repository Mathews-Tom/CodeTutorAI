"""
CodeTutorAI - Base Node

This module contains the base Node class for the CodeTutorAI workflow.
"""


class Node:
    """Base class for all workflow nodes."""

    def process(self, context):
        """Process the node's task using the given context.

        Args:
            context (dict): The shared context dictionary.

        Returns:
            dict or None: Updates to the context, or None if the context is updated directly.
        """
        raise NotImplementedError("Subclasses must implement the process method.")
