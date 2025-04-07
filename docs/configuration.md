# Configuration Guide

EnlightenAI provides various configuration options to customize the tutorial generation process. This guide explains how to configure EnlightenAI for your specific needs.

## Environment Variables

EnlightenAI uses environment variables for sensitive information like API keys. You can set these in a `.env` file in your project directory:

```bash
# Required for OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Required for Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for Google PaLM
GOOGLE_API_KEY=your_google_api_key_here
```

## Command-Line Options

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `repo_url` | URL of the GitHub repository to analyze | (Required) |
| `--output-dir` | Output directory for the tutorial | `tutorial_output` |
| `--web-url` | URL of a website with additional information | None |
| `--verbose`, `-v` | Enable verbose output | False |

### LLM Options

| Option | Description | Default |
|--------|-------------|---------|
| `--llm-provider` | LLM provider to use (openai, anthropic, palm) | `openai` |
| `--api-key` | API key for the LLM provider | From environment |

### Repository Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-file-size` | Maximum file size in bytes to include | 1MB (1048576) |
| `--max-files` | Maximum number of files to include | 100 |
| `--include-patterns` | Comma-separated list of file patterns to include | None (all files) |
| `--exclude-patterns` | Comma-separated list of file patterns to exclude | None |
| `--fetch-repo-metadata` | Fetch repository metadata (stars, forks, etc.) | False |

### Content Generation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-chunk-size` | Maximum chunk size in characters for LLM analysis | 5000 |
| `--ordering-method` | Method for chapter ordering (auto, topological, learning_curve, llm) | `auto` |
| `--batch-size` | Number of chapters to generate in parallel | 1 |
| `--output-formats` | Comma-separated list of output formats | `markdown` |

## Output Formats

EnlightenAI supports the following output formats:

- **markdown**: Generate Markdown files
- **html**: Generate a single-page HTML version
- **pdf**: Generate a PDF-ready Markdown file
- **github_pages**: Generate GitHub Pages configuration

## Advanced Configuration

### Customizing Templates

EnlightenAI uses templates for generating content. You can customize these templates by modifying the source code:

- **Chapter Templates**: Located in `src/enlightenai/nodes/write_chapters.py`
- **Index Template**: Located in `src/enlightenai/nodes/combine_tutorial.py`
- **HTML Template**: Located in `src/enlightenai/nodes/combine_tutorial.py`

### Customizing LLM Parameters

You can customize LLM parameters by modifying the source code:

- **Temperature**: Controls the randomness of the output
- **Max Tokens**: Controls the maximum length of the output
- **System Message**: Controls the initial instructions to the LLM

These parameters can be found in the `src/enlightenai/utils/llm_client.py` file.

## Example Configuration

Here's an example of a complete configuration using command-line options:

```bash
enlightenai https://github.com/username/repository \
  --output-dir ./docs \
  --web-url https://docs.example.com \
  --include "*.py,*.md" \
  --exclude "test_*,*__pycache__*" \
  --llm-provider openai \
  --max-file-size 524288 \
  --max-files 50 \
  --max-chunk-size 4000 \
  --ordering-method learning_curve \
  --batch-size 2 \
  --output-formats markdown,html,pdf \
  --fetch-repo-metadata \
  --verbose
```
