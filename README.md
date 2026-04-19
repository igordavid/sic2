# sic2 — Secret Scanner for Source Code

A fast, lightweight Python tool that scans source code repositories for leaked secrets — API keys, tokens, passwords, and credentials — before they end up in production or get committed to version control.

---

## Features

- **7 built-in detection rules** covering AWS credentials, GitHub tokens, and generic API keys
- **Recursive directory scanning** with smart filtering (skips `.git`, `node_modules`, `.venv`, binaries, etc.)
- **Two output formats** — human-readable text with color, or JSON for CI/CD integration
- **Severity levels** — HIGH / MEDIUM to prioritize remediation
- **CI-friendly exit codes** — exits `1` when secrets are found, `0` when clean
- **Precise reporting** — exact file path, line number, matched text, and surrounding context
- **Resilient** — handles encoding issues and unreadable files gracefully

---

## Installation

```bash
git clone https://github.com/your-username/sic2.git
cd sic2

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

---

## Usage

```bash
# Scan a directory
sic2 scan /path/to/your/project

# Scan a single file
sic2 scan config.env

# JSON output (for CI/CD pipelines or further processing)
sic2 scan /path/to/project --format json

# Disable color (useful in scripts or non-TTY environments)
sic2 scan /path/to/project --no-colour

# You can also run it as a module
python -m sic2 scan /path/to/project
```

### Example output

```
[HIGH]   AWS Access Key ID
         src/config.py:14
         Match : AKIAIOSFODNN7EXAMPLE
         Line  : AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"

[HIGH]   GitHub Classic PAT
         .env:3
         Match : ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
         Line  : GITHUB_TOKEN=ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456

Found 2 secret(s). Review and rotate them immediately.
```

---

## Detected Secret Types

| Rule ID | Type | Severity |
|---|---|---|
| `AWS001` | AWS Access Key ID (`AKIA…`) | HIGH |
| `AWS002` | AWS Secret Access Key | HIGH |
| `GH001` | GitHub Classic PAT (`ghp_…`) | HIGH |
| `GH002` | GitHub Fine-Grained PAT (`github_pat_…`) | HIGH |
| `GH003` | GitHub OAuth Token (`gho_…`) | HIGH |
| `GH004` | GitHub App Installation Token (`ghs_…`) | HIGH |
| `GEN001` | Generic API Key assignment | MEDIUM |

---

## Architecture

```
cli.py          ← Command-line interface (Click)
scanner.py      ← File traversal and pattern matching
rules.py        ← Regex-based detection rules
reporter.py     ← Output formatting (text / JSON)
```

Data flows one way: **CLI → Scanner → Reporter**. Adding a new secret type means adding one entry to `rules.py`. Changing output formats only touches `reporter.py`.

---

## Development

```bash
# Run tests
pytest

# Run a specific test
pytest tests/test_scanner.py::test_name -v

# Lint and format
ruff check .
ruff format .
```

---

## CI/CD Integration

sic2 exits with code `1` if any secrets are found, making it easy to fail a pipeline:

```yaml
# GitHub Actions example
- name: Scan for secrets
  run: |
    pip install sic2
    sic2 scan . --format json
```

---

## Requirements

- Python 3.10+
- Click 8.1+

---

## License

MIT
