# Usage Guide

EnlightenAI provides a simple yet powerful interface for generating tutorials from GitHub repositories. This guide will walk you through the basic and advanced usage of EnlightenAI.

## Basic Usage

### As a Command-Line Tool

After installation, you can run EnlightenAI directly from the command line:

```bash
enlightenai https://github.com/username/repository --output-dir ./docs
```

### As a Python Module

You can also run EnlightenAI as a Python module:

```bash
python -m enlightenai.cli https://github.com/username/repository --output-dir ./docs
```

## Command-Line Options

EnlightenAI provides various command-line options to customize the tutorial generation process:

```bash
# Basic options
enlightenai https://github.com/username/repository --output-dir ./docs --verbose

# Specify web documentation to include
enlightenai https://github.com/username/repository --web-url https://docs.example.com

# Filter files to include/exclude
enlightenai https://github.com/username/repository --include "*.py,*.md" --exclude "test_*,*__pycache__*"

# Choose LLM provider
enlightenai https://github.com/username/repository --llm-provider openai

# Override API key
enlightenai https://github.com/username/repository --api-key YOUR_API_KEY

# Parallel processing
enlightenai https://github.com/username/repository --batch-size 2

# Multiple output formats
enlightenai https://github.com/username/repository --output-formats markdown,html,pdf,github_pages
```

## Output Formats

EnlightenAI supports multiple output formats:

- **markdown**: Generate Markdown files (default)
- **html**: Generate a single-page HTML version
- **pdf**: Generate a PDF-ready Markdown file
- **github_pages**: Generate GitHub Pages configuration

Example:

```bash
enlightenai https://github.com/username/repository --output-formats markdown,html,pdf
```

## Testing with Mock Data

You can test EnlightenAI with mock data to avoid making actual API calls:

```bash
python -m enlightenai.test_mock --verbose
```

## Advanced Usage

### Customizing Chapter Ordering

EnlightenAI provides multiple methods for ordering chapters:

```bash
# Auto (default)
enlightenai https://github.com/username/repository --ordering-method auto

# Topological ordering
enlightenai https://github.com/username/repository --ordering-method topological

# Learning curve ordering
enlightenai https://github.com/username/repository --ordering-method learning_curve

# LLM-based ordering
enlightenai https://github.com/username/repository --ordering-method llm
```

### Limiting Repository Size

For large repositories, you can limit the number of files and file size:

```bash
# Limit to 50 files
enlightenai https://github.com/username/repository --max-files 50

# Limit file size to 500KB
enlightenai https://github.com/username/repository --max-file-size 512000
```

### Fetching Repository Metadata

You can include repository metadata (stars, forks, etc.) in the tutorial:

```bash
enlightenai https://github.com/username/repository --fetch-repo-metadata
```

## Examples

### Generate a tutorial for FastAPI

```bash
enlightenai https://github.com/tiangolo/fastapi --output-formats markdown,html
```

### Generate a tutorial for NumPy with custom ordering

```bash
enlightenai https://github.com/numpy/numpy --ordering-method learning_curve --max-files 30
```

### Generate a tutorial for a small project with all options

```bash
enlightenai https://github.com/username/small-project \
  --output-dir ./docs \
  --web-url https://docs.example.com \
  --include "*.py,*.md" \
  --exclude "test_*,*__pycache__*" \
  --llm-provider openai \
  --batch-size 2 \
  --output-formats markdown,html,pdf,github_pages \
  --ordering-method learning_curve \
  --fetch-repo-metadata \
  --verbose
```
