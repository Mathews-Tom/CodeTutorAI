# Contributing to EnlightenAI

Thank you for your interest in contributing to EnlightenAI! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## Getting Started

1. **Fork the repository**:
   - Visit [https://github.com/Mathews-Tom/EnlightenAI](https://github.com/Mathews-Tom/EnlightenAI)
   - Click the "Fork" button in the top-right corner

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/EnlightenAI.git
   cd EnlightenAI
   ```

3. **Set up the development environment**:
   ```bash
   # Install in development mode
   ./install_dev.sh
   ```

4. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. **Make your changes**:
   - Write code that follows the project's style and conventions
   - Add or update tests as necessary
   - Update documentation to reflect your changes

2. **Run tests**:
   ```bash
   # Run tests with mock data
   python -m enlightenai.test_mock --verbose
   ```

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add your meaningful commit message here"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a pull request**:
   - Visit your fork on GitHub
   - Click "New Pull Request"
   - Select your branch and provide a description of your changes
   - Submit the pull request

## Project Structure

The project follows a src-based package structure:

```
EnlightenAI/
├── src/                  # Source code directory
│   └── enlightenai/      # Main package
│       ├── __init__.py    # Package initialization
│       ├── cli.py         # CLI entry point
│       ├── flow.py        # Defines the AI workflow
│       ├── nodes/         # Node implementations for each step
│       │   ├── ...
│       └── utils/         # Utility scripts
│           ├── ...
├── docs/                  # Documentation
├── assets/                # Project assets
├── setup.py               # Package setup script
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single task
- Write unit tests for new functionality

## Pull Request Guidelines

- Keep pull requests focused on a single change
- Update documentation to reflect your changes
- Add or update tests as necessary
- Ensure all tests pass before submitting
- Follow the pull request template

## Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the [issue tracker](https://github.com/Mathews-Tom/EnlightenAI/issues)
2. If not, create a new issue with a descriptive title and detailed description
3. Include steps to reproduce the issue, expected behavior, and actual behavior
4. Include your environment details (OS, Python version, etc.)

## Feature Requests

If you have an idea for a new feature:

1. Check if the feature has already been requested in the [issue tracker](https://github.com/Mathews-Tom/EnlightenAI/issues)
2. If not, create a new issue with a descriptive title and detailed description
3. Explain why the feature would be useful to users
4. Suggest an implementation approach if possible

## License

By contributing to EnlightenAI, you agree that your contributions will be licensed under the project's [MIT License](license.md).
