# test_scanner.py — integration tests for the scanner module.
#
# "Integration tests" check that multiple components work correctly together.
# Here we write real files to a temporary directory on disk and verify that
# scan_path() finds the secrets we planted (and ignores what it should ignore).
#
# pytest provides the `tmp_path` fixture automatically: it gives each test its
# own empty temporary directory that is cleaned up after the test finishes.

from pathlib import Path


from sic2.scanner import scan_path


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def write_file(directory: Path, filename: str, content: str) -> Path:
    """Create a file inside *directory* with the given *content* and return its path."""
    file_path = directory / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_scan_finds_aws_key(tmp_path: Path):
    """Scanner should detect an AWS Access Key ID in a Python file."""
    write_file(tmp_path, "config.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

    findings = scan_path(tmp_path)

    # There should be exactly one finding.
    assert len(findings) == 1
    assert findings[0].rule.id == "aws-access-key"
    assert findings[0].line_no == 1


def test_scan_finds_github_token(tmp_path: Path):
    """Scanner should detect a GitHub classic PAT."""
    token = "ghp_" + "Z" * 36
    write_file(tmp_path, "deploy.sh", f'export GH_TOKEN="{token}"\n')

    findings = scan_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].rule.id == "github-pat-classic"


def test_scan_clean_file_returns_no_findings(tmp_path: Path):
    """A file with no secrets should produce zero findings."""
    write_file(tmp_path, "hello.py", 'print("Hello, world!")\n')

    findings = scan_path(tmp_path)

    assert findings == []


def test_scan_multiple_secrets_in_one_file(tmp_path: Path):
    """Each secret on a different line should each produce its own finding."""
    token = "ghp_" + "A" * 36
    content = (
        'aws_key = "AKIAIOSFODNN7EXAMPLE"\n'
        f'github_token = "{token}"\n'
    )
    write_file(tmp_path, "secrets.env", content)

    findings = scan_path(tmp_path)
    rule_ids = {f.rule.id for f in findings}  # set of matched rule IDs

    assert "aws-access-key" in rule_ids
    assert "github-pat-classic" in rule_ids


def test_scan_skips_binary_extension(tmp_path: Path):
    """Files with binary extensions (e.g. .png) should be skipped entirely."""
    # Even though the content looks like a secret, the file has a .png extension.
    write_file(tmp_path, "image.png", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

    findings = scan_path(tmp_path)

    assert findings == []


def test_scan_skips_venv_directory(tmp_path: Path):
    """The scanner should not descend into virtual-environment directories."""
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    write_file(venv_dir, "site.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

    findings = scan_path(tmp_path)

    assert findings == []


def test_scan_single_file(tmp_path: Path):
    """Passing a single file path (not a directory) should work correctly."""
    file_path = write_file(tmp_path, "creds.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

    findings = scan_path(file_path)  # pass the FILE, not the directory

    assert len(findings) == 1


def test_scan_reports_correct_line_number(tmp_path: Path):
    """The line number in the finding should match where the secret actually appears."""
    content = (
        "# This is a comment\n"   # line 1
        "import os\n"             # line 2
        'key = "AKIAIOSFODNN7EXAMPLE"\n'  # line 3
    )
    write_file(tmp_path, "app.py", content)

    findings = scan_path(tmp_path)

    assert len(findings) == 1
    assert findings[0].line_no == 3
