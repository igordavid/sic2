# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python application for scanning source code repositories for leaked secrets (API keys, tokens, passwords, credentials, etc.).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Common Commands

```bash
# Run the scanner
python -m sic2 scan <path>

# Run tests
pytest

# Run a single test
pytest tests/test_scanner.py::test_name -v

# Lint
ruff check .
ruff format .
```

## Architecture

To be documented as the project grows. Key areas to define:

- **Rules engine** — patterns (regex or otherwise) that identify secrets by type
- **Scanner core** — file traversal, content reading, rule matching
- **Reporter** — output formatting (stdout, JSON, SARIF, etc.)
- **Ignore/allowlist** — mechanisms to suppress false positives
