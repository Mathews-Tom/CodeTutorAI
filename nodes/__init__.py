"""
EnlightenAI - Workflow Nodes

This package contains the node classes for the EnlightenAI tutorial generation workflow.
Each node performs a specific task in the pipeline and passes its results to the next node.
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
