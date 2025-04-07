```
 ______      _ _       _     _              _    ___
|  ____|    | (_)     | |   | |            | |  |__ \
| |__   _ __| |_  __ _| |__ | |_ ___ _ __  / \     ) |
|  __| | '_ \ | |/ _` | '_ \| __/ _ \ '_ \/ _ \   / /
| |____| | | | | | (_| | | | | ||  __/ | / ___ \ / /_
|______|_| |_|_|_|\__, |_| |_|\__\___|_|/_/   \_\____|
                   __/ |
                  |___/
```

# 🌟 🔍 EnlightenAI – Illuminate the Hidden Logic Within Codebases

>*Lost in someone else's GitHub project? Build an AI Code Explainer to generate clear explanations! This tutorial shows you how to create an agent that analyzes repositories and produces easy-to-understand guides.*

**EnlightenAI** is an AI-powered system that transforms any GitHub repository into a beginner-friendly, tutorial-style walkthrough. It analyzes the structure, abstractions, and relationships within a codebase to produce a multi-chapter guide that helps you deeply understand the inner workings of unfamiliar projects.

---

## 🔍 What Is EnlightenAI?

EnlightenAI acts as a digital oracle for codebases — using AI to reveal the design, purpose, and interactions between the components of any GitHub repository. Think of it as a magnifying glass for developers who want to uncover the story behind someone else’s code.

### Core Features

- 🧠 Uses LLMs to identify and explain key abstractions
- 🕸️ Maps out relationships and architecture visually
- 📘 Generates structured Markdown tutorials
- 🌐 Output is ready for GitHub Pages or docs hosting

---

## ⚙️ How It Works

EnlightenAI operates as a modular AI workflow that progresses through the following steps:

```mermaid
graph TD
    A[Start] --> B[FetchRepo]
    B --> C[IdentifyAbstractions]
    C --> D[AnalyzeRelationships]
    D --> E[OrderChapters]
    E --> F[WriteChapters]
    F --> G[CombineTutorial]
    G --> H[Generate Markdown Docs]
```

Each node is powered by prompts to a large language model (LLM), enabling intelligent interpretation of even complex, multi-language codebases.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Mathews-Tom/EnlightenAI.git
cd EnlightenAI
```

### 2. Install Dependencies

#### Using pip

```bash
# Install from the current directory
pip install -e .

# Or install directly from GitHub
pip install git+https://github.com/Mathews-Tom/EnlightenAI.git
```

#### Using uv (faster installation)

```bash
# Install uv if you don't have it
pip install uv

# Install from the current directory
uv pip install -e .

# Or install directly from GitHub
uv pip install git+https://github.com/Mathews-Tom/EnlightenAI.git
```

#### For Development

```bash
# Using the provided script
./install_dev.sh

# Or manually
pip install -e .
```

### 3. Set Up Environment Variables

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key_here
# Optional: Add other API keys if needed
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
```

### 4. Run EnlightenAI on a GitHub Repo

#### As a Command-Line Tool

After installation, you can run EnlightenAI directly from the command line:

```bash
# Using the command-line tool
enlightenai https://github.com/SomeUser/SomeProject --output-dir ./docs
```

#### As a Python Module

You can also run EnlightenAI as a Python module:

```bash
# Using Python module syntax
python -m enlightenai.cli https://github.com/SomeUser/SomeProject --output-dir ./docs

# Or with python3 explicitly
python3 -m enlightenai.cli https://github.com/SomeUser/SomeProject --output-dir ./docs
```

#### Optional Flags

```bash
  --web-url https://example.com/docs  # Additional web context
  --include "*.py,*.md"               # File patterns to include
  --exclude "test_*,*__pycache__*"    # File patterns to exclude
  --llm-provider openai               # LLM provider (openai, anthropic, palm)
  --api-key YOUR_API_KEY              # Override API key from .env
  --batch-size 2                      # Number of chapters to generate in parallel
  --output-formats markdown,html,pdf  # Output formats to generate
  --verbose                           # Enable verbose output
```

### 5. Run with Mock Data for Testing

You can test EnlightenAI with mock data to avoid making actual API calls:

```bash
# Using Python module syntax
python -m enlightenai.test_mock --verbose

# Or with python3 explicitly
python3 -m enlightenai.test_mock --verbose

# With additional options
python -m enlightenai.test_mock --output-formats markdown,html --batch-size 2 --verbose
```

---

## 🧱 Folder Structure

```plaintext
EnlightenAI/
├── src/                  # Source code directory
│   └── enlightenai/      # Main package
│       ├── __init__.py    # Package initialization
│       ├── cli.py         # CLI entry point
│       ├── flow.py        # Defines the AI workflow
│       ├── nodes/         # Node implementations for each step
│       │   ├── __init__.py # Node package initialization
│       │   ├── node.py     # Base Node class
│       │   ├── fetch_repo_gitin.py # GitHub repository fetching
│       │   ├── fetch_web.py # Web content fetching
│       │   ├── identify_abstractions.py # Abstraction identification
│       │   ├── analyze_relationships.py # Relationship analysis
│       │   ├── order_chapters.py # Chapter ordering
│       │   ├── write_chapters.py # Chapter writing
│       │   └── combine_tutorial.py # Tutorial combination
│       ├── test_enlightenai.py # Test script for real data
│       ├── test_mock.py    # Test script for mock data
│       └── utils/         # Utility scripts
│           ├── __init__.py # Utils package initialization
│           ├── call_llm.py # LLM client compatibility layer
│           ├── llm_client.py # Enhanced LLM client
│           ├── formatting.py # Formatting utilities
│           └── mock_data.py # Mock data for testing
├── docs/                  # Output tutorials
├── assets/                # Project assets
├── setup.py               # Package setup script
├── requirements.txt       # Python dependencies
├── install_dev.sh         # Development installation script
├── .env.example           # Example environment variables
├── implementation_plan.md # Implementation plan
├── LICENSE                # MIT License
└── README.md              # You're here!
```

---

## 📘 Example Outputs

EnlightenAI generates comprehensive tutorials for any GitHub repository. Here are some examples:

### FastAPI Tutorial

A comprehensive tutorial explaining the FastAPI framework, including its routing system, dependency injection, and more.

[View FastAPI Tutorial](docs/examples/fastapi/index.md)

### NumPy Tutorial

A detailed walkthrough of the NumPy library, covering arrays, broadcasting, universal functions, and more.

[View NumPy Tutorial](docs/examples/numpy/index.md)

### AutoGen Tutorial

An in-depth explanation of the AutoGen framework for building multi-agent systems with LLMs.

[View AutoGen Tutorial](docs/examples/autogen/index.md)

### Try It Yourself

Generate your own tutorial by running:

```bash
# As a command-line tool
enlightenai https://github.com/username/repository

# Or as a Python module
python -m enlightenai.cli https://github.com/username/repository
```

---

## 🛠 Tech Stack

- **Python**
- **LLMs** (configurable: OpenAI, Anthropic Claude, Google PaLM)
- **Custom Flow Engine** for workflow orchestration
- **gitin** for GitHub repository crawling
- **crawl4ai** for web content crawling
- **tqdm** for progress tracking
- **Markdown + MermaidJS** for documentation

---

## 📄 License

MIT License. See `LICENSE` for details.

## 🧙‍♂️🌀 “The Oracle’s Lens” - Banner Concept

An ancient yet futuristic magnifying lens floats above a glowing, semi-transparent scroll of symbolic code. Under the lens, cryptic symbols shift into radiant patterns, revealing insights or illuminated shapes — as if the AI oracle is interpreting the code’s hidden meaning.

### 🎨 Visual Elements

- Floating Magnifier: Suspended mid-air, glowing faintly (gold, silver, or ethereal blue), with ornate or arcane designs etched into the rim
- Digital Scroll: A holographic or semi-paper scroll unrolling below, filled with mysterious glyphs, symbols, or flowing syntax-like patterns
- Revealed Area: The magnifier reveals a different “truth” — glowing connections, diagrams, or an “enlightened” region on the scroll
- Background: A mystical space with floating particles, soft constellations or runes in the background — cosmic but subtle
- Typography (optional): The name EnlightenAI in elegant, slightly serif or script-like typeface, glowing or carved into the background

### 🧠 Mood

- Mystical AI scribe meets digital prophet
- Blends ancient aesthetics (scroll, symbols) with a futuristic, magical HUD feel
- Tells the story of revealing what was always there, hidden beneath the code

### 🖼️ Composition

- Banner-style (wider than tall) to fit GitHub headers (ideal: 1280x400 or scalable)
- Magnifier centered or slightly off-center with radiating light
- Scroll wraps across bottom or diagonally with abstract symbols flowing along it

---

> Built with 🔮 by [Mathews Tom](https://github.com/Mathews-Tom)
