# ✅ EnlightenAI Implementation Plan

This roadmap covers architecture, core modules, development phases, and deliverables — from initial repo analysis to tutorial generation.

## 🧠 Project Goal Recap

Create an AI system that analyzes a GitHub codebase and generates a structured, multi-chapter, tutorial-style walkthrough explaining its inner workings — using LLMs and symbolic code analysis.

## 📌 Phase 1: Project Setup & Core Workflow Engine

### ✅ Objectives:

- Set up project structure and CLI
- Integrate PocketFlow or custom workflow framework
- Define the flow of steps: fetch → analyze → explain → compile

### 📂 Tasks:

- Set up basic repo structure (main.py, flow.py, nodes/, utils/)
- Define CLI interface (argparse) with input flags
- Build create_tutorial_flow() to chain nodes
- Establish shared context for node communication (e.g., repo path, files)

## 📌 Phase 2: GitHub Repo Crawler

### ✅ Objectives:

- Clone or fetch files from a public GitHub repo
- Filter by include/exclude patterns
- Store source files in memory for further analysis

### 📂 Tasks:

- Build utils/crawl_github.py using GitHub API
- Add file filtering logic (extensions, path patterns, size limit)
- Store files as { path, content } objects in shared state

## 📌 Phase 3: Abstraction Identification (LLM)

### ✅ Objectives:

- Use an LLM to analyze files and identify key abstractions/components
- Return structured data (e.g., JSON or YAML with name, desc, file refs)

### 📂 Tasks:

- Create nodes/identify_abstractions.py
- Format prompt + file summaries for LLM
- Parse structured response into components list
- Validate for correctness and handle LLM errors

## 📌 Phase 4: Relationship Analysis (LLM)

### ✅ Objectives:

- Analyze how components interact (calls, imports, dependencies)
- Generate a relationship map and project summary

### 📂 Tasks:

- Create nodes/analyze_relationships.py
- Pass abstractions to LLM for interaction mapping
- Parse response into relationship graph (e.g., edges: A -> B)
- Create Mermaid-compatible relationship data

## 📌 Phase 5: Tutorial Chapter Ordering

### ✅ Objectives:

- Generate a logical order for explaining components (based on dependencies)
- This defines the tutorial chapter sequence

### 📂 Tasks:

- Create nodes/order_chapters.py
- Use topological sort or LLM suggestion for sequence
- Output list of chapter indices and names

## 📌 Phase 6: Chapter Generation (LLM)

### ✅ Objectives:

- Generate Markdown content for each component
- Include descriptions, code examples, and cross-references

### 📂 Tasks:

- Create nodes/write_chapters.py (ideally as a batch processor)
- Prompt LLM with abstraction details + related code
- Post-process to format Markdown (headers, code blocks)
- Save to docs/ as chapter_X_component.md

## 📌 Phase 7: Tutorial Compilation

### ✅ Objectives:

- Merge all chapters into a complete tutorial set
- Generate index file with summary and diagrams

### 📂 Tasks:

- Create nodes/combine_tutorial.py
- Build index.md with intro, table of contents, and Mermaid diagram
- Ensure all files are navigable and GitHub Pages–ready

## 📌 Phase 8: LLM Abstraction Layer

### ✅ Objectives:

- Create a flexible interface to support different LLM providers (OpenAI, Claude, PaLM)

📂 Tasks:

- Build utils/llm_client.py
- Wrap prompt → response functionality
- Load API key from env/config and support swapping providers
- Include error handling, retries, and token limits

## 📌 Phase 9: Documentation + Demo Outputs

### ✅ Objectives:

- Generate sample outputs (e.g., for FastAPI, NumPy, AutoGen)
- Polish documentation and onboarding experience

### 📂 Tasks:

- Update README.md with usage examples + banner
- Add example projects in docs/examples/
- Create GitHub Pages config (_config.yml or MkDocs)
- Add contribution guide, license, etc.

## ## 📌 Phase 10 (Optional): Enhancements & UI

🔮 Stretch Goals:

- Add CLI options for depth, format (PDF/HTML), or language
- Add Mermaid visual enhancements (e.g., class diagrams)
- Add optional IDE or browser-based viewer
- Host as an online tool (repo input → hosted tutorial output)

📁 Final Directory Structure

```bash
EnlightenAI/
├── main.py
├── flow.py
├── nodes/
│   ├── fetch_repo.py
│   ├── identify_abstractions.py
│   ├── analyze_relationships.py
│   ├── order_chapters.py
│   ├── write_chapters.py
│   └── combine_tutorial.py
├── utils/
│   ├── crawl_github.py
│   ├── llm_client.py
│   └── formatting.py
├── docs/
│   ├── index.md
│   ├── chapter_*.md
│   └── examples/
├── assets/
│   └── banner.png
├── README.md
└── requirements.txt
```

## 🗂️ Deliverables Summary

- CLI script (main.py)
- Modular node workflow (flow.py + nodes/)
- LLM abstraction layer
- Full Markdown tutorial output
- Examples and live demos
- Clean documentation with visuals
