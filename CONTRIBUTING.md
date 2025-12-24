# Contributing to QuickSpin AI

Thank you for your interest in contributing to QuickSpin AI! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Install dependencies**:
   ```bash
   make dev
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run locally**:
   ```bash
   make run
   ```

## Code Style

We follow strict Python code standards:

- **Type hints**: All functions must have full type annotations
- **Line length**: 100 characters (enforced by Black and Ruff)
- **Docstrings**: Google-style docstrings for all public functions
- **Async/await**: Use async/await for all I/O operations

### Running Code Quality Checks

```bash
# Format code
make format

# Run linters
make lint

# Type checking
uv run mypy app/
```

## Testing

All new features should include tests:

```bash
# Run tests
make test

# Run with coverage
make test-cov
```

Test files should be placed in `tests/` directory and follow the naming convention `test_*.py`.

## Pull Request Process

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for your changes

4. **Run quality checks**:
   ```bash
   make format
   make lint
   make test
   ```

5. **Commit your changes** with descriptive commit messages

6. **Push to your fork** and create a pull request

7. **Describe your changes** in the PR description

## Project Structure

- `app/core/`: Configuration and core utilities
- `app/models/`: Pydantic models for data validation
- `app/repositories/`: Data access layer (MongoDB, ChromaDB)
- `app/services/`: Business logic services
- `app/workflows/`: LangGraph workflows for AI operations
- `app/routers/`: FastAPI endpoint handlers
- `tests/`: Test suite

## Adding New Features

### Adding a New Workflow

1. Create workflow file in `app/workflows/`
2. Implement workflow class with LangGraph
3. Add workflow to AI engine service
4. Add tests in `tests/test_workflows/`

### Adding a New API Endpoint

1. Create or update router in `app/routers/`
2. Define request/response models in `app/models/`
3. Add endpoint to router
4. Include router in `app/main.py`
5. Add tests in `tests/test_api/`

### Extending Knowledge Base

Add new knowledge in `app/repositories/knowledge_repo.py` in the `seed_knowledge_base()` method.

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages and stack traces

## Questions?

Feel free to open an issue for questions or discussions about contributing.
