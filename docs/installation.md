# Installation Guide

EnlightenAI can be installed using various methods. Choose the one that best suits your needs.

## Prerequisites

- Python 3.8 or higher
- pip or uv package manager
- Git (for installation from GitHub)

## Installation Methods

### Using pip

```bash
# Install from PyPI (coming soon)
pip install enlightenai

# Or install directly from GitHub
pip install git+https://github.com/Mathews-Tom/EnlightenAI.git
```

### Using uv (faster installation)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

```bash
# Install uv if you don't have it
pip install uv

# Install EnlightenAI using uv
uv pip install git+https://github.com/Mathews-Tom/EnlightenAI.git
```

### Development Installation

If you want to contribute to EnlightenAI or modify the code, you can install it in development mode:

```bash
# Clone the repository
git clone https://github.com/Mathews-Tom/EnlightenAI.git
cd EnlightenAI

# Install in development mode
./install_dev.sh

# Or manually
pip install -e .
```

## Setting Up API Keys

EnlightenAI uses language models from various providers. You'll need to set up API keys for the providers you want to use.

Create a `.env` file in your project directory with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key_here
# Optional: Add other API keys if needed
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
```

## Verifying Installation

To verify that EnlightenAI is installed correctly, run:

```bash
# Check the version
enlightenai --version

# Or run the help command
enlightenai --help
```

## Troubleshooting

If you encounter any issues during installation, try the following:

1. Make sure you have the latest version of pip:
   ```bash
   pip install --upgrade pip
   ```

2. Check that you have the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. If you're using a virtual environment, make sure it's activated:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. If you're still having issues, please [open an issue](https://github.com/Mathews-Tom/EnlightenAI/issues) on GitHub.
