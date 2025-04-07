"""
EnlightenAI - Workflow Engine

This module defines the tutorial generation workflow using a simple node-based
pipeline architecture. Each node in the workflow performs a specific task and
passes its results to the next node through a shared context dictionary.
"""

import sys
import time
from datetime import timedelta

from tqdm import tqdm
from tqdm.auto import tqdm as auto_tqdm

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
        # Add a progress manager to the context
        context["progress_manager"] = ProgressManager()

        # Create a progress bar for the overall workflow
        with tqdm(
            total=len(self.nodes),
            desc="Overall Progress",
            unit="node",
            position=0,
            leave=True,
        ) as main_pbar:
            for i, node in enumerate(self.nodes):
                # Update the main progress bar description
                node_name = node.__class__.__name__
                main_pbar.set_description(f"[{i + 1}/{len(self.nodes)}] {node_name}")

                # Print node information if verbose
                if context.get("verbose"):
                    print(
                        f"\n{'=' * 80}\nRunning node {i + 1}/{len(self.nodes)}: {node_name}\n{'=' * 80}"
                    )

                # Set the current node in the progress manager
                context["progress_manager"].set_current_node(node_name)

                # Create a nested progress bar for the node
                with tqdm(desc=f"  {node_name}", position=1, leave=False) as node_pbar:
                    # Add the node progress bar to the context
                    context["progress_manager"].set_node_pbar(node_pbar)

                    # Execute the node and update the context
                    start_time = time.time()
                    node_result = node.process(context)
                    elapsed_time = time.time() - start_time

                    # Nodes can return None if they update the context directly
                    if node_result is not None:
                        context.update(node_result)

                    # Ensure the node progress bar is at 100%
                    node_pbar.n = 100
                    node_pbar.refresh()

                # Update the main progress bar
                main_pbar.update(1)

                # Get elapsed time from progress manager if available
                if "progress_manager" in context:
                    _, time_str = context["progress_manager"].get_elapsed_time(
                        node_name
                    )
                    print(
                        f"\nCompleted {node_name} in {time_str} (total: {elapsed_time:.2f} seconds)"
                    )
                else:
                    # Format elapsed time as HH:MM:SS
                    hours, remainder = divmod(elapsed_time, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

                    # Print completion message
                    print(
                        f"\nCompleted {node_name} in {time_str} (total: {elapsed_time:.2f} seconds)"
                    )

        # Remove the progress manager from the context
        del context["progress_manager"]

        return context


class ProgressManager:
    """A class for managing progress bars in the workflow."""

    def __init__(self):
        """Initialize the progress manager."""
        self.current_node = None
        self.node_pbar = None
        self.task_pbars = {}
        self.start_times = {}

    def set_current_node(self, node_name):
        """Set the current node being processed.

        Args:
            node_name (str): The name of the current node
        """
        self.current_node = node_name
        self.task_pbars = {}
        self.start_times[node_name] = time.time()

    def set_node_pbar(self, pbar):
        """Set the progress bar for the current node.

        Args:
            pbar (tqdm): The progress bar for the node
        """
        self.node_pbar = pbar

    def update_node_progress(self, progress, total=100):
        """Update the progress of the current node.

        Args:
            progress (int): The current progress value
            total (int, optional): The total progress value
        """
        if self.node_pbar:
            self.node_pbar.n = int((progress / total) * 100)
            self.node_pbar.refresh()

    def get_task_pbar(self, task_name, total, desc=None, unit="it", position=2):
        """Get or create a progress bar for a specific task.

        Args:
            task_name (str): The name of the task
            total (int): The total number of items
            desc (str, optional): The description of the progress bar
            unit (str, optional): The unit of the progress bar
            position (int, optional): The position of the progress bar

        Returns:
            tqdm: The progress bar for the task, or None if total is 0
        """
        # Don't create a progress bar if there's nothing to process
        if total <= 0:
            return None

        if task_name not in self.task_pbars:
            desc = desc or f"    {task_name}"
            self.task_pbars[task_name] = tqdm(
                total=total, desc=desc, unit=unit, position=position, leave=False
            )
        return self.task_pbars[task_name]

    def close_task_pbar(self, task_name):
        """Close a task progress bar.

        Args:
            task_name (str): The name of the task
        """
        if task_name in self.task_pbars:
            self.task_pbars[task_name].close()
            del self.task_pbars[task_name]

    def get_elapsed_time(self, node_name=None):
        """Get the elapsed time for a node.

        Args:
            node_name (str, optional): The name of the node. If None, uses the current node.

        Returns:
            float: The elapsed time in seconds
            str: The formatted time string (HH:MM:SS)
        """
        node_name = node_name or self.current_node
        if node_name in self.start_times:
            elapsed_time = time.time() - self.start_times[node_name]

            # Format as HH:MM:SS
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

            return elapsed_time, time_str

        return 0, "00:00:00"


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
