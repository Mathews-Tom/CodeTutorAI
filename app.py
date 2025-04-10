import os
import re  # Import regex module
import shutil  # Import for rmtree
import sys
from pathlib import Path

import diskcache  # Import diskcache for clearing
import streamlit as st

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

# sys.path modification removed as package is installed via `pip install -e .`

load_dotenv()

try:
    from codetutorai.flow import create_tutorial_flow
    from codetutorai.utils.constants import DEFAULT_CACHE_DIR, DEFAULT_OUTPUT_DIR
    from codetutorai.utils.formatting import (
        format_duration,
        get_repo_info_from_url,
        is_valid_github_url,
    )
    from codetutorai.utils.history_manager import (  # Added import
        DEFAULT_HISTORY_FILENAME,
        load_github_url_history,
        save_generation_metadata,
    )
    from codetutorai.utils.html_viewer import (
        open_html_viewer,  # Import the viewer function
    )
except ImportError as e:
    import traceback

    st.error(
        f"Could not import CodeTutorAI modules. Specific error: {e}\n"  # Renamed
        f"Traceback:\n{traceback.format_exc()}\n\n"
        "Make sure CodeTutorAI and all its dependencies are installed correctly "  # Renamed
        "in the '.venv' environment and the script is run from the project root."
    )
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="CodeTutorAI Tutorial Generator", layout="wide"
)  # Renamed


# --- Initialize Session State ---
def init_session_state():
    defaults = {
        "repo_url": "",
        "web_url": "",
        "output_dir": DEFAULT_OUTPUT_DIR,
        "depth": "intermediate",
        "language": "en",
        "output_formats": ["markdown", "viewer"],  # Default updated
        "generate_diagrams": True,  # Default updated
        "open_viewer": True,  # Default updated
        "llm_provider": "OpenAI",
        "llm_model": "GPT-4O",
        "api_key": "",
        "max_file_size": 1048576,
        "max_files": 100,
        "include_patterns": "",
        "exclude_patterns": "",
        "fetch_repo_metadata": False,
        "max_chunk_size": 5000,
        "ordering_method": "auto",
        "batch_size": 1,
        "cache_enabled": True,  # Default updated
        "cache_dir": DEFAULT_CACHE_DIR,
        "force_regeneration": False,  # Added state for forcing regeneration
        "running": False,  # Flag to indicate if generation is in progress
        "status_message": "",
        "progress_value": 0.0,
        "result_message": "",
        "viewer_path": None,  # Store path to viewer HTML if generated
        # "view_results_enabled" flag removed, will rely directly on path existence
        "viewer_auto_opened": False,  # Flag to track if viewer was opened automatically (May remove later if new approach works)
        "last_successful_viewer_path": None,  # Persists path for manual button
        "confirm_clear_output": False,  # Flag for confirmation step
    }
    # Original logic: Only set if key doesn't exist
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# Helper function moved to formatting.py
# --- UI Layout ---
st.title("CodeTutorAI  🧑‍🏫 💻 🤖: Understand Codebases Faster")  # Renamed
st.markdown("Your AI-powered guide through any GitHub repo.")

# --- Input Area ---
st.header("Input URLs")
# --- GitHub URL Input with History ---
# Load history (consider caching this or loading once per session if slow)
history_file = Path(st.session_state.output_dir) / DEFAULT_HISTORY_FILENAME
url_history = load_github_url_history(history_file)

# Prepare options for the selectbox
add_new_option = "-- Add New URL --"
selectbox_options = [add_new_option] + url_history

# Determine the initial index for the selectbox
try:
    # If current URL is valid and in history, select it
    if st.session_state.repo_url and st.session_state.repo_url in url_history:
        current_selection_index = selectbox_options.index(st.session_state.repo_url)
    else:
        # Default to "Add New" if current URL is empty or not in history
        current_selection_index = 0  # Index of add_new_option
except ValueError:
    # Fallback if something unexpected happens
    current_selection_index = 0

# Display the selectbox
selected_option = st.selectbox(
    "GitHub Repository URL*",
    selectbox_options,
    index=current_selection_index,
    disabled=st.session_state.running,
    help="Select a previously used URL or choose 'Add New URL'.",
)

# Display text input only if "Add New" is selected
new_repo_url = ""
if selected_option == add_new_option:
    new_repo_url = st.text_input(
        "Enter New GitHub URL:",
        value="",  # Start empty for new input
        placeholder="https://github.com/user/repo",
        disabled=st.session_state.running,
        key="new_repo_url_input",  # Add key for state management
    )
    # Update session state based on the text input
    st.session_state.repo_url = new_repo_url
else:
    # Update session state based on the selection from history
    st.session_state.repo_url = selected_option

# Note: The is_valid_github_url check used for the generate button
# will now use the updated st.session_state.repo_url value.
# --- End GitHub URL Input ---
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
            key="output_formats",  # Bind to st.session_state.output_formats
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
        st.session_state.force_regeneration = st.checkbox(
            "Force Regeneration (ignore cache)",
            value=st.session_state.force_regeneration,
            disabled=st.session_state.running,
            help="If checked, LLM calls will not use cached results and will overwrite existing cache entries.",
            key="force_regen_checkbox",  # Added key for clarity
        )

with st.expander("LLM & API"):
    col1, col2 = st.columns(2)
    with col1:
        # Define provider options with user-friendly names
        llm_provider_options = ["OpenAI", "Anthropic", "Google"]
        st.session_state.llm_provider = st.selectbox(
            "LLM Provider",
            llm_provider_options,
            # Find the index of the current session state value in the new options list
            index=llm_provider_options.index(st.session_state.llm_provider),
            disabled=st.session_state.running,
        )
        # --- Dynamic Model Selection ---
        # Define models for each provider (using user-friendly names)
        # TODO: Confirm the exact API model IDs if they differ from display names
        # Updated model lists based on user feedback
        models_by_provider = {
            "Google": [
                "Gemini 1.5 Flash",  # Default
                "Gemini 1.5 Pro",
                "Gemini 2.0 Flash",
                "Gemini 2.5 Pro Preview",
            ],
            "OpenAI": [
                "GPT-4O",
                "GPT-4 Turbo",
                "GPT-4",
                "GPT-3.5 Turbo",
            ],
            "Anthropic": [
                "Claude 3.5 Haiku",  # Defaulting to cheaper/faster Sonnet/Haiku
                "Claude 3.5 Sonnet",
                "Claude 3.7 Sonnet",
                "Claude 3 Opus",
            ],
        }

        # Get the models for the currently selected provider
        current_provider = st.session_state.llm_provider
        available_models = models_by_provider.get(current_provider, [])

        # Determine the index for the model selectbox
        # Check if the current model exists within the available models for the selected provider
        current_model_in_list = st.session_state.llm_model in available_models

        if current_model_in_list:
            model_index = available_models.index(st.session_state.llm_model)
        elif available_models:
            # If current model is not valid for this provider, default index to 0 (first model)
            # Let the selectbox widget update the session state on the next interaction/rerun
            model_index = 0
        else:
            # No models available, set index to 0 (selectbox will be empty/disabled)
            model_index = 0

        st.session_state.llm_model = st.selectbox(
            "Model",
            available_models,
            index=model_index,
            disabled=st.session_state.running
            or not available_models,  # Disable if no models
            key="llm_model_selector",  # Add key for potential state management needs
            help="Select the specific model to use for generation.",
        )
    with col2:
        st.session_state.api_key = st.text_input(
            "API Key",  # Removed (Optional)
            value=st.session_state.api_key,
            type="password",
            help="Required if not set as environment variable (e.g., GOOGLE_API_KEY, OPENAI_API_KEY)",  # Updated help text
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
        # Add Clear Cache button below the checkbox
        clear_cache_button = st.button(
            "Clear Cache",
            disabled=st.session_state.running or not st.session_state.cache_enabled,
            help="Deletes all cached LLM responses from the specified cache directory.",
        )
    with col2:
        st.session_state.cache_dir = st.text_input(
            "Cache Directory",
            value=st.session_state.cache_dir,
            disabled=st.session_state.running or not st.session_state.cache_enabled,
        )

# Debugging block moved further down

# --- Action Buttons ---
st.header("Actions")
col1, col2, col3, col4 = st.columns(4)  # Back to 4 columns

with col1:
    # Check if the repo URL is valid
    is_url_valid = is_valid_github_url(st.session_state.repo_url)
    generate_button = st.button(
        "Generate Tutorial",
        type="primary",
        # Disable if running OR if the URL is invalid/empty
        disabled=st.session_state.running or not is_url_valid,
        help="Start generating the tutorial for the specified repository.",  # Added tooltip
    )

# Removed misplaced clear_output_button definition from col1

with col2:  # View Results button
    # Add View Results button, disabled initially and when running
    # Debugging removed
    view_results_button = st.button(
        "View Results",
        # Simplified: Enable only if a persistent viewer path exists (ignoring os.path.exists for now)
        disabled=not st.session_state.get(
            "last_successful_viewer_path"
        ),  # Use .get() for safety
        key="view_results_btn",  # Added explicit key
        help="Open the generated HTML viewer for the last successful run.",  # Added tooltip
    )

with col3:  # Add Clear Output button here
    clear_output_button = st.button(
        "Clear Output",
        disabled=st.session_state.running
        or not is_url_valid,  # Keep disabled if no valid URL
        help="Delete generated output for the current repo, or all outputs.",  # Updated tooltip
    )

with col4:  # Reset Application button
    reset_button = st.button(
        "Reset Application",
        type="secondary",
        help="Resets all inputs and session state to defaults.",
    )  # Renamed button
# --- Confirmation Logic for Clear Output ---
if st.session_state.get("confirm_clear_output", False):
    st.warning("⚠️ Are you sure you want to clear generated output?")

    # Determine specific repo path
    specific_repo_path_str = "N/A"
    output_subdir_path = None
    if is_valid_github_url(st.session_state.repo_url):
        repo_info = get_repo_info_from_url(st.session_state.repo_url)
        if repo_info:
            repo_subdir_name = f"{repo_info['username']}_{repo_info['repo_name']}"
            output_subdir_path = Path(st.session_state.output_dir) / repo_subdir_name
            specific_repo_path_str = str(output_subdir_path)

    confirm_col1, confirm_col2, confirm_col3 = st.columns(3)

    with confirm_col1:
        # Button to clear only the specific repo's output
        confirm_clear_specific = st.button(
            f"Clear Specific Output ({specific_repo_path_str})",
            type="primary",
            disabled=not (
                output_subdir_path
                and output_subdir_path.exists()
                and output_subdir_path.is_dir()
            ),
        )

    with confirm_col2:
        # Button to clear the entire output directory
        base_output_dir_path = Path(st.session_state.output_dir)
        confirm_clear_all = st.button(
            f"Clear ALL Outputs in ({st.session_state.output_dir})",
            disabled=not (
                base_output_dir_path.exists() and base_output_dir_path.is_dir()
            ),
        )

    with confirm_col3:
        cancel_clear = st.button("Cancel")

    if confirm_clear_specific and output_subdir_path:
        try:
            shutil.rmtree(output_subdir_path)
            st.success(f"Successfully deleted: {output_subdir_path}")
            st.session_state.viewer_path = None  # Clear related state
            st.session_state.last_successful_viewer_path = None
            st.session_state.confirm_clear_output = False  # Hide confirmation
            st.rerun()
        except OSError as e:
            st.error(f"Error deleting {output_subdir_path}: {e}")
            st.session_state.confirm_clear_output = (
                False  # Hide confirmation on error too
            )
            st.rerun()

    if confirm_clear_all:
        try:
            # Iterate and remove subdirectories
            deleted_dir_count = 0
            deleted_history = False
            history_file_path = (
                base_output_dir_path / DEFAULT_HISTORY_FILENAME
            )  # Get history file path

            for item in base_output_dir_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    deleted_dir_count += 1
                elif item == history_file_path:  # Check if it's the history file
                    try:
                        item.unlink()  # Delete the history file
                        deleted_history = True
                    except OSError as e_hist:
                        st.warning(
                            f"Could not delete history file {item.name}: {e_hist}"
                        )
                # Other files are implicitly kept now

            # Report deletion status
            success_msg = (
                f"Deleted {deleted_dir_count} subdirectories in {base_output_dir_path}."
            )
            if deleted_history:
                success_msg += f" Deleted {DEFAULT_HISTORY_FILENAME}."
            st.success(success_msg)
            st.session_state.viewer_path = None  # Clear related state
            st.session_state.last_successful_viewer_path = None
            st.session_state.confirm_clear_output = False  # Hide confirmation
            st.rerun()
        except OSError as e:
            st.error(f"Error clearing subdirectories in {base_output_dir_path}: {e}")
            st.session_state.confirm_clear_output = (
                False  # Hide confirmation on error too
            )
            st.rerun()

    if cancel_clear:
        st.session_state.confirm_clear_output = False  # Hide confirmation
        st.rerun()

# --- Status/Progress Area ---
# Define result placeholder outside the conditional block to show final status
result_placeholder = st.empty()

if st.session_state.running:
    # Show progress header and placeholders only when running
    st.header("Progress")
    status_placeholder = st.empty()
    progress_placeholder = st.empty()

    # Update status and progress bar
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
# "Clear Inputs" button and logic removed
# Logic for the Clear Cache button (added in the Caching expander)
if "clear_cache_button" in locals() and clear_cache_button:
    cache_dir_path = Path(st.session_state.cache_dir)
    if cache_dir_path.exists() and cache_dir_path.is_dir():
        try:
            # Use diskcache to clear the cache directory
            cache = diskcache.Cache(str(cache_dir_path))
            cache.clear()
            cache.close()  # Important to close the cache object
            st.success(f"Cache cleared successfully at: {cache_dir_path}")
            # Optionally remove the directory itself if empty, but clearing contents is safer
            # if not any(cache_dir_path.iterdir()):
            #     cache_dir_path.rmdir()
        except Exception as e:
            st.error(f"Error clearing cache: {e}")
    else:
        st.warning(f"Cache directory not found or is not a directory: {cache_dir_path}")
    # No rerun needed, just display message
# Logic for the Clear Output button
if "clear_output_button" in locals() and clear_output_button:
    # Set flag to show confirmation options
    st.session_state.confirm_clear_output = True
    st.rerun()  # Rerun to display confirmation

if generate_button:
    # Initial validation for GitHub URL (already implicitly handled by button disable state, but good practice)
    if not is_valid_github_url(st.session_state.repo_url):
        st.error("A valid GitHub Repository URL is required.")
    else:
        # --- API Key Validation ---
        api_key_present = False
        selected_provider = (
            st.session_state.llm_provider.lower()
        )  # Ensure lowercase for matching
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            # "palm": "GOOGLE_API_KEY", # Keep or remove based on final Google provider name
            "google": "GOOGLE_API_KEY",
        }
        env_var = env_var_map.get(selected_provider)

        if st.session_state.api_key:
            api_key_present = True
            api_key_source = "input field"
        elif env_var and os.environ.get(env_var):
            api_key_present = True
            api_key_source = f"environment variable ({env_var})"
        # --- End API Key Validation ---

        if not api_key_present:
            st.error(
                f"API Key for {st.session_state.llm_provider} is missing. Please provide it in the input field or set the '{env_var}' environment variable."
            )
        else:
            # Proceed with generation if URL and API key are valid
            st.info(
                f"Using API key from {api_key_source}."
            )  # Optional: Inform user where key was found
            st.session_state.running = True
            st.session_state.status_message = "Starting generation..."
            st.session_state.progress_value = 0.0
            st.session_state.result_message = ""
            st.session_state.viewer_path = None  # Reset viewer path on new run
            st.session_state.viewer_auto_opened = False  # Reset auto-open flag
            st.session_state.view_results_enabled = (
                False  # Disable view button on new run
            )
            st.rerun()  # Rerun to disable inputs and show progress

if "reset_button" in locals() and reset_button:
    # Clear all existing session state keys first
    st.info("Resetting application state...")
    keys_to_clear = list(st.session_state.keys())  # Get keys before iterating
    for key in keys_to_clear:
        del st.session_state[key]
    # Now initialize with defaults
    init_session_state()
    # No need to clear messages explicitly, init_session_state handles it now
    st.rerun()  # Rerun to reflect cleared inputs and state

# --- Generation Logic (Placeholder) ---
if st.session_state.running:
    # --- Prepare Output Directory ---
    repo_info = get_repo_info_from_url(st.session_state.repo_url)
    if not repo_info:
        # This case should ideally not be reached due to button disabling logic
        st.error("Invalid GitHub URL detected during context creation.")
        st.session_state.running = False  # Stop running state
        st.rerun()  # Rerun to show error and re-enable inputs
        st.stop()  # Stop script execution for this run

    repo_subdir_name = f"{repo_info['username']}_{repo_info['repo_name']}"
    # Ensure the base output directory exists
    base_output_dir = Path(st.session_state.output_dir)
    try:
        base_output_dir.mkdir(parents=True, exist_ok=True)
        repo_output_dir = base_output_dir / repo_subdir_name
        repo_output_dir.mkdir(parents=True, exist_ok=True)
        final_output_dir = str(
            repo_output_dir
        )  # Use the specific repo dir for the flow
        st.session_state.current_output_dir = (
            final_output_dir  # Store for potential later use (e.g., success message)
        )
    except OSError as e:
        st.error(f"Failed to create output directory: {e}")
        st.session_state.running = False
        st.rerun()
        st.stop()
    # --- End Prepare Output Directory ---

    # Construct context dictionary
    context = {
        "repo_url": st.session_state.repo_url,
        "output_dir": final_output_dir,  # Use the specific repo output directory
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
        "force_regeneration": st.session_state.force_regeneration,  # Pass force flag
        "progress_callback": streamlit_progress_callback,  # Pass the actual callback
    }

    # --- Actual flow execution ---
    st.info(
        f"Generating tutorial in: {final_output_dir}"
    )  # Inform user about the output location
    try:
        # The callback is already defined globally and assigned to context at line 310
        # No need to redefine or reassign here

        # Record start time
        start_time = time.time()

        # Create and run the flow, get final context
        flow = create_tutorial_flow()
        final_context = flow.run(context)  # Get the final context back

        # Record end time and calculate duration
        end_time = time.time()
        duration = end_time - start_time
        # Removed debug block
        # Removed duplicated debug block

        # --- Success ---
        output_location = st.session_state.get(
            "current_output_dir", final_output_dir
        )  # Use the specific output dir
        # Add duration to the success message
        st.session_state.result_message = f"Tutorial generated successfully in {output_location} (took {format_duration(duration)})"  # Use new formatter
        # Add note about cache status based on settings and timing heuristic
        cache_status_note = ""
        CACHE_HIT_THRESHOLD_SECONDS = 5  # Heuristic threshold

        if not st.session_state.cache_enabled:
            cache_status_note = "(Cache was disabled)"
        elif st.session_state.force_regeneration:
            if duration < CACHE_HIT_THRESHOLD_SECONDS:
                # Likely hit rate limit or other fast error, didn't truly regenerate
                cache_status_note = "(Forced regeneration attempted - likely failed fast, cache not updated)"
            else:
                # Took longer, assume successful forced regeneration
                cache_status_note = "(Forced regeneration - cache updated)"
        else:  # Cache enabled, not forcing
            if duration < CACHE_HIT_THRESHOLD_SECONDS:
                cache_status_note = "(Result likely from cache)"
            else:
                # Took longer, likely a cache miss or first run
                cache_status_note = "(Cache enabled - likely cache miss or first run)"

        st.session_state.result_message += f" {cache_status_note}"

        st.session_state.status_message = "Completed!"
        st.session_state.progress_value = 1.0
        # st.session_state.view_results_enabled = True # Removed - will rely on path check

        # --- Save Metadata ---
        try:
            metadata_to_save = {
                # Use context for values passed to the flow
                "repo_url": context.get("repo_url"),
                "output_path": output_location,  # The specific repo output dir
                "llm_provider": context.get("llm_provider"),
                "llm_model": st.session_state.llm_model,  # Get selected model from state
                "depth": context.get("depth"),
                "language": context.get("language"),
                "output_formats": context.get("output_formats"),
                "generate_diagrams": context.get("generate_diagrams"),
                "cache_enabled": context.get("cache_enabled"),
                "force_regeneration": context.get("force_regeneration"),
                # Add other relevant config if needed
            }
            # Define history file path (in the base output directory)
            history_file = Path(st.session_state.output_dir) / DEFAULT_HISTORY_FILENAME
            save_generation_metadata(metadata_to_save, history_file)
        except Exception as meta_err:
            st.warning(f"Could not save generation metadata: {meta_err}")
        # --- End Save Metadata ---
        # Removed stray closing parenthesis from here
        st.session_state.status_message = "Completed!"
        st.session_state.progress_value = 1.0
        # view_results_enabled moved below

        # Check if viewer was generated and path exists in context
        # Assuming the CombineTutorialNode adds 'viewer_html_path' to context
        viewer_path = final_context.get(
            "viewer_html_path"
        )  # Get path directly from context
        # Debugging lines removed
        if viewer_path and os.path.exists(viewer_path):
            # Set both the temporary path for auto-open and the persistent path for manual button
            st.session_state.viewer_path = viewer_path
            st.session_state.last_successful_viewer_path = viewer_path
            # Enable button only if viewer path is valid
            st.session_state.view_results_enabled = True
            # Auto-opening logic moved outside the generation block
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
        # Preserve the viewer path before resetting running state
        temp_viewer_path = st.session_state.get("last_successful_viewer_path")
        # Ensure running state is reset
        st.session_state.running = False
        # Removed preservation logic - state should persist normally
        st.rerun()  # Re-adding rerun to see if it affects state persistence timing
# Debugging lines removed

# --- View Results Button Logic ---
if view_results_button:
    # Use the persistent path for the manual button
    path_to_view = st.session_state.last_successful_viewer_path
    if path_to_view and os.path.exists(path_to_view):
        try:
            open_html_viewer(path_to_view)
        except Exception as view_err:
            st.error(f"Could not open viewer: {view_err}")
    else:
        st.warning(
            "Viewer HTML path not found or file does not exist. Cannot open viewer."
        )

        # --- Automatic Viewer Opening Logic (Decoupled) ---
        # This runs *after* the generation block has finished and state is updated
        # Check if auto-open is enabled and a valid temporary viewer path exists
        if (
            st.session_state.open_viewer
            and st.session_state.viewer_path
            and os.path.exists(st.session_state.viewer_path)
        ):
            viewer_path_to_open = st.session_state.viewer_path
            # Clear the temporary path immediately to prevent re-opening on rerun
            st.session_state.viewer_path = None
            try:
                open_html_viewer(viewer_path_to_open)
                st.toast("Viewer opened automatically.")
            except Exception as view_err:
                st.warning(f"Could not automatically open viewer: {view_err}")
            # No need for viewer_auto_opened flag with this approach
        # --- End Automatic Viewer Opening ---

        # --- Add Footer or other elements if needed ---
# st.sidebar.info("...")
# --- Add Footer or other elements if needed ---
# st.sidebar.info("...")
