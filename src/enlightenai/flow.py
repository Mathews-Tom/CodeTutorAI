"""
EnlightenAI - Workflow Engine

This module defines the tutorial generation workflow using a simple node-based
pipeline architecture. Each node in the workflow performs a specific task and
passes its results to the next node through a shared context dictionary.
"""

from tqdm import tqdm

from enlightenai.nodes.analyze_relationships import AnalyzeRelationshipsNode
from enlightenai.nodes.combine_tutorial import CombineTutorialNode
from enlightenai.nodes.fetch_repo_gitin import FetchRepoGitinNode
from enlightenai.nodes.fetch_web import FetchWebNode
from enlightenai.nodes.identify_abstractions import IdentifyAbstractionsNode
from enlightenai.nodes.order_chapters import OrderChaptersNode
from enlightenai.nodes.write_chapters import WriteChaptersNode


class Flow:
    """A simple workflow engine that executes a series of nodes in sequence."""

    def __init__(self, nodes=None):
        """Initialize a new Flow with the given nodes.

        Args:
            nodes (list): A list of Node objects to execute in sequence.
        """
        self.nodes = nodes or []

    def add_node(self, node):
        """Add a node to the workflow.

        Args:
            node: A Node object to add to the workflow.
        """
        self.nodes.append(node)

    def run(self, context):
        """Execute all nodes in the workflow in sequence.

        Args:
            context (dict): A shared context dictionary that is passed to each node.
                Each node can read from and write to this context.

        Returns:
            dict: The final context after all nodes have executed.
        """
        # Create a progress bar for the nodes
        with tqdm(total=len(self.nodes), desc="Processing", unit="node") as pbar:
            for i, node in enumerate(self.nodes):
                # Update the progress bar description
                pbar.set_description(f"Processing {node.__class__.__name__}")

                if context.get("verbose"):
                    print(
                        f"\nRunning node {i + 1}/{len(self.nodes)}: {node.__class__.__name__}"
                    )

                # Execute the node and update the context
                node_result = node.process(context)

                # Nodes can return None if they update the context directly
                if node_result is not None:
                    context.update(node_result)

                # Update the progress bar
                pbar.update(1)

        return context


def create_tutorial_flow():
    """Create the EnlightenAI tutorial generation workflow.

    Returns:
        Flow: A configured Flow object with all necessary nodes.
    """
    flow = Flow()

    # Add nodes in the order they should execute
    flow.add_node(FetchRepoGitinNode())
    flow.add_node(FetchWebNode())
    flow.add_node(IdentifyAbstractionsNode())
    flow.add_node(AnalyzeRelationshipsNode())
    flow.add_node(OrderChaptersNode())
    flow.add_node(WriteChaptersNode())
    flow.add_node(CombineTutorialNode())

    return flow
