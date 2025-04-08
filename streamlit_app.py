import os
import sys
from pathlib import Path

import streamlit as st

# sys.path modification removed as package is installed via `pip install -e .`

try:
    from enlightenai.flow import create_tutorial_flow
    from enlightenai.utils.constants import DEFAULT_CACHE_DIR, DEFAULT_OUTPUT_DIR
    from enlightenai.utils.html_viewer import (
        open_html_viewer,
    )  # Import the viewer function
except ImportError as e:
    import traceback

    st.error(
        f"Could not import EnlightenAI modules. Specific error: {e}\n"
        f"Traceback:\n{traceback.format_exc()}\n\n"
        "Make sure EnlightenAI and all its dependencies are installed correctly "
        "in the '.venv' environment and the script is run from the project root."
    )
    st.stop()

# --- Page Configuration ---
st.set_page_config(page_title="EnlightenAI Tutorial Generator", layout="wide")


# --- Initialize Session State ---
def init_session_state():
    defaults = {
        "repo_url": "",
        "web_url": "",
        "output_dir": DEFAULT_OUTPUT_DIR,
        "depth": "intermediate",
        "language": "en",
        "output_formats": ["markdown"],
        "generate_diagrams": False,
        "open_viewer": False,
        "llm_provider": "openai",
        "api_key": "",
        "max_file_size": 1048576,
        "max_files": 100,
        "include_patterns": "",
        "exclude_patterns": "",
        "fetch_repo_metadata": False,
        "max_chunk_size": 5000,
        "ordering_method": "auto",
        "batch_size": 1,
        "cache_enabled": False,
        "cache_dir": DEFAULT_CACHE_DIR,
        "running": False,  # Flag to indicate if generation is in progress
        "status_message": "",
        "progress_value": 0.0,
        "result_message": "",
        "viewer_path": None,  # Store path to viewer HTML if generated
        "view_results_enabled": False,  # Control state of the view results button
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# --- UI Layout ---
st.title("💡 EnlightenAI: Demystify Codebases 🔑")
st.markdown("Generate programming tutorials automatically from GitHub repositories.")

# --- Input Area ---
st.header("Input URLs")
st.session_state.repo_url = st.text_input(
    "GitHub Repository URL*",
    value=st.session_state.repo_url,
    placeholder="https://github.com/user/repo",
    disabled=st.session_state.running,
)
st.session_state.web_url = st.text_input(
    "Website URL (Optional)",
    value=st.session_state.web_url,
    placeholder="https://project-website.com",
    disabled=st.session_state.running,
)

# --- Configuration Area ---
st.header("Configuration Options")

with st.expander("Basic Options", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.output_dir = st.text_input(
            "Output Directory",
            value=st.session_state.output_dir,
            disabled=st.session_state.running,
        )
        st.session_state.depth = st.selectbox(
            "Tutorial Depth",
            ["basic", "intermediate", "advanced"],
            index=["basic", "intermediate", "advanced"].index(st.session_state.depth),
            disabled=st.session_state.running,
        )
        st.session_state.language = st.text_input(
            "Tutorial Language (ISO 639-1)",
            value=st.session_state.language,
            disabled=st.session_state.running,
        )
    with col2:
        # Use the 'key' argument to bind the widget to session state
        st.multiselect(
            "Output Formats (markdown, html, pdf, github_pages, viewer)",
            ["markdown", "html", "pdf", "github_pages", "viewer"],
            # default parameter removed; key handles initial value from session state
            key="output_formats", # Bind to st.session_state.output_formats
            disabled=st.session_state.running,
        )
        st.session_state.generate_diagrams = st.checkbox(
            "Generate Diagrams",
            value=st.session_state.generate_diagrams,
            disabled=st.session_state.running,
        )
        st.session_state.open_viewer = st.checkbox(
            "Open Viewer After Generation",
            value=st.session_state.open_viewer,
            disabled=st.session_state.running,
        )

with st.expander("LLM & API"):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.llm_provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic", "palm"],
            index=["openai", "anthropic", "palm"].index(st.session_state.llm_provider),
            disabled=st.session_state.running,
        )
    with col2:
        st.session_state.api_key = st.text_input(
            "API Key (Optional)",
            value=st.session_state.api_key,
            type="password",
            help="Leave blank to use environment variable (e.g., OPENAI_API_KEY)",
            disabled=st.session_state.running,
        )

with st.expander("File Handling"):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.max_file_size = st.number_input(
            "Max File Size (bytes)",
            min_value=1,
            value=st.session_state.max_file_size,
            disabled=st.session_state.running,
        )
        st.session_state.max_files = st.number_input(
            "Max Files",
            min_value=1,
            value=st.session_state.max_files,
            disabled=st.session_state.running,
        )
        st.session_state.fetch_repo_metadata = st.checkbox(
            "Fetch Repo Metadata",
            value=st.session_state.fetch_repo_metadata,
            disabled=st.session_state.running,
        )
    with col2:
        st.session_state.include_patterns = st.text_input(
            "Include Patterns (comma-sep)",
            value=st.session_state.include_patterns,
            placeholder="*.py,*.js",
            disabled=st.session_state.running,
        )
        st.session_state.exclude_patterns = st.text_input(
            "Exclude Patterns (comma-sep)",
            value=st.session_state.exclude_patterns,
            placeholder="*.md,*.txt",
            disabled=st.session_state.running,
        )

with st.expander("Advanced Generation"):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.max_chunk_size = st.number_input(
            "Max Chunk Size (chars)",
            min_value=100,
            value=st.session_state.max_chunk_size,
            disabled=st.session_state.running,
        )
    with col2:
        st.session_state.ordering_method = st.selectbox(
            "Chapter Ordering Method",
            ["auto", "topological", "learning_curve", "llm"],
            index=["auto", "topological", "learning_curve", "llm"].index(
                st.session_state.ordering_method
            ),
            disabled=st.session_state.running,
        )
    st.session_state.batch_size = st.number_input(
        "Batch Size (Parallel Chapters)",
        min_value=1,
        value=st.session_state.batch_size,
        disabled=st.session_state.running,
    )


with st.expander("Caching"):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.cache_enabled = st.checkbox(
            "Enable LLM Cache",
            value=st.session_state.cache_enabled,
            disabled=st.session_state.running,
        )
    with col2:
        st.session_state.cache_dir = st.text_input(
            "Cache Directory",
            value=st.session_state.cache_dir,
            disabled=st.session_state.running or not st.session_state.cache_enabled,
        )

# --- Action Buttons ---
st.header("Actions")
col1, col2, col3, _ = st.columns([1, 1, 1, 2])  # Adjust column ratios for 3 buttons

with col1:
    generate_button = st.button(
        "Generate Tutorial", type="primary", disabled=st.session_state.running
    )

with col2:
    clear_button = st.button("Clear Inputs", disabled=st.session_state.running)

with col3:
    # Add View Results button, disabled initially and when running
    view_results_button = st.button(
        "View Results",
        disabled=not st.session_state.view_results_enabled or st.session_state.running,
    )

# --- Status/Progress Area ---
st.header("Progress")
status_placeholder = st.empty()
progress_placeholder = st.empty()
result_placeholder = st.empty()

if st.session_state.running:
    status_placeholder.info(st.session_state.status_message)
    progress_placeholder.progress(st.session_state.progress_value)
elif st.session_state.result_message:
    if "Error" in st.session_state.result_message:
        result_placeholder.error(st.session_state.result_message)
    else:
        result_placeholder.success(st.session_state.result_message)

# --- Callback Function ---
# Define this outside the main generation block so it's available when context is created
import time  # Ensure time is imported globally if needed by the callback


def streamlit_progress_callback(message: str, progress: float):
    """Callback function to update Streamlit UI elements."""
    st.session_state.status_message = message
    st.session_state.progress_value = progress
    # Use placeholders directly for updates within the callback
    # Note: Placeholders need to be defined in the main scope to be accessible here
    # We'll ensure they are defined before the generation logic runs.
    try:
        status_placeholder.info(st.session_state.status_message)
        progress_placeholder.progress(st.session_state.progress_value)
        # Small sleep to allow UI to update smoothly
        time.sleep(0.01)
    except NameError:
        # Fallback if placeholders aren't defined yet (e.g., during initial run)
        print(f"Progress Update (UI not ready): {message} - {progress:.2f}")
        pass


# --- Button Logic ---
if clear_button:
    # Reset all session state keys to their defaults
    init_session_state()
    # Clear status/result messages
    st.session_state.status_message = ""
    st.session_state.progress_value = 0.0
    st.session_state.result_message = ""
    st.session_state.viewer_path = None  # Reset viewer path on clear
    st.session_state.view_results_enabled = False  # Disable view button on clear
    st.rerun()  # Rerun to reflect cleared inputs

if generate_button:
    if not st.session_state.repo_url:
        st.error("GitHub Repository URL is required.")
    else:
        st.session_state.running = True
        st.session_state.status_message = "Starting generation..."
        st.session_state.progress_value = 0.0
        st.session_state.result_message = ""
        st.session_state.viewer_path = None  # Reset viewer path on new run
        st.session_state.view_results_enabled = False  # Disable view button on new run
        st.rerun()  # Rerun to disable inputs and show progress

# --- Generation Logic (Placeholder) ---
if st.session_state.running:
    # Construct context dictionary (Removed debug print)
    context = {
        "repo_url": st.session_state.repo_url,
        "output_dir": st.session_state.output_dir,
        "web_url": st.session_state.web_url or None,  # Handle empty string
        "llm_provider": st.session_state.llm_provider,
        "api_key": st.session_state.api_key or None,  # Handle empty string
        "max_file_size": st.session_state.max_file_size,
        "max_files": st.session_state.max_files,
        "include_patterns": st.session_state.include_patterns.split(",")
        if st.session_state.include_patterns
        else None,
        "exclude_patterns": st.session_state.exclude_patterns.split(",")
        if st.session_state.exclude_patterns
        else None,
        "max_chunk_size": st.session_state.max_chunk_size,
        "batch_size": st.session_state.batch_size,
        "output_formats": st.session_state.output_formats,
        "ordering_method": st.session_state.ordering_method,
        "fetch_repo_metadata": st.session_state.fetch_repo_metadata,
        "verbose": False,  # Can be added as an option if needed
        "depth": st.session_state.depth,
        "language": st.session_state.language,
        "generate_diagrams": st.session_state.generate_diagrams,
        "open_viewer": st.session_state.open_viewer,
        "cache_enabled": st.session_state.cache_enabled,
        "cache_dir": st.session_state.cache_dir,
        "progress_callback": streamlit_progress_callback,  # Pass the actual callback
    }

    # --- Actual flow execution ---
    try:
        # The callback is already defined globally and assigned to context at line 310
        # No need to redefine or reassign here

        # Create and run the flow, get final context
        flow = create_tutorial_flow()
        final_context = flow.run(context)  # Get the final context back
        # Removed debug block
        # Removed duplicated debug block

        # --- Success ---
        st.session_state.result_message = (
            f"Tutorial generated successfully in {st.session_state.output_dir}"
        )
        st.session_state.status_message = "Completed!"
        st.session_state.progress_value = 1.0
        st.session_state.view_results_enabled = True  # Enable view button

        # Check if viewer was generated and path exists in context
        # Assuming the CombineTutorialNode adds 'viewer_html_path' to context
        viewer_path = final_context.get("viewer_html_path") # Get path directly from context
        if viewer_path and os.path.exists(viewer_path):
            st.session_state.viewer_path = viewer_path
            # Open viewer automatically if requested
            if st.session_state.open_viewer:
                try:
                    open_html_viewer(viewer_path)
                    st.session_state.result_message += " Viewer opened."
                except Exception as view_err:
                    st.warning(f"Could not automatically open viewer: {view_err}")
        elif (
            st.session_state.open_viewer and "viewer" in st.session_state.output_formats
        ):
            st.warning(
                "Viewer output format selected, but viewer path not found in context or file doesn't exist."
            )

    except Exception as e:
        # Error handling
        st.session_state.result_message = f"Error during generation: {str(e)}"
        import traceback

        st.error(
            f"Full error details:\n{traceback.format_exc()}"
        )  # Show full traceback in Streamlit

    finally:
        # Ensure running state is reset and trigger a rerun
        st.session_state.running = False
        st.rerun()

# --- View Results Button Logic ---
if view_results_button:
    if st.session_state.viewer_path and os.path.exists(st.session_state.viewer_path):
        try:
            open_html_viewer(st.session_state.viewer_path)
        except Exception as view_err:
            st.error(f"Could not open viewer: {view_err}")
    else:
        st.warning(
            "Viewer HTML path not found or file does not exist. Cannot open viewer."
        )


# --- Add Footer or other elements if needed ---
# st.sidebar.info("...")
# --- Add Footer or other elements if needed ---
# st.sidebar.info("...")
