# test_scanner.py — unit and integration tests for the scanner module.
#
# UNIT TESTS: Test individual scanner functions in isolation (_should_skip_file, etc.)
# INTEGRATION TESTS: Test scan_path() with real files in temporary directories
#
# pytest provides the `tmp_path` fixture automatically: it gives each test its
# own empty temporary directory that is cleaned up after the test finishes.

import pytest
from pathlib import Path

from sic2.scanner import (
    scan_path,
    _should_skip_file,
    _should_skip_dir,
    _scan_file,
    Finding,
    BINARY_EXTENSIONS,
    SKIP_DIRS,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def write_file(directory: Path, filename: str, content: str) -> Path:
    """Create a file inside *directory* with the given *content* and return its path."""
    file_path = directory / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# UNIT TESTS: _should_skip_file()
# ---------------------------------------------------------------------------

class TestShouldSkipFile:
    """Test file filtering (binary extensions, generated files)."""

    @pytest.mark.parametrize("extension", [
        ".png", ".jpg", ".gif", ".pdf", ".zip",
        ".pyc", ".pyo", ".whl", ".exe", ".so",
    ])
    def test_skips_binary_extensions(self, extension: str):
        """Binary/generated files should be skipped."""
        path = Path(f"file{extension}")
        assert _should_skip_file(path) is True

    @pytest.mark.parametrize("extension", [
        ".py", ".js", ".ts", ".go", ".java", ".c",
        ".sh", ".env", ".json", ".yaml", ".txt",
    ])
    def test_does_not_skip_source_extensions(self, extension: str):
        """Source code files should NOT be skipped."""
        path = Path(f"file{extension}")
        assert _should_skip_file(path) is False

    def test_case_insensitive(self):
        """Extension check should be case-insensitive."""
        assert _should_skip_file(Path("image.PNG")) is True
        assert _should_skip_file(Path("archive.ZIP")) is True
        assert _should_skip_file(Path("script.PY")) is False

    def test_no_extension(self):
        """Files with no extension should not be skipped (unless binary detected another way)."""
        path = Path("Makefile")
        assert _should_skip_file(path) is False


# ---------------------------------------------------------------------------
# UNIT TESTS: _should_skip_dir()
# ---------------------------------------------------------------------------

class TestShouldSkipDir:
    """Test directory filtering (venv, .git, node_modules, etc.)."""

    @pytest.mark.parametrize("dirname", [
        ".git", ".venv", ".hg", ".svn",
        "__pycache__", "node_modules", ".yarn",
        "dist", "build", ".mypy_cache",
    ])
    def test_skips_generated_and_cache_dirs(self, dirname: str):
        """Generated, cache, and dependency directories should be skipped."""
        assert _should_skip_dir(dirname) is True

    @pytest.mark.parametrize("dirname", [
        "src", "tests", "lib", "app",
        "utils", "config", "scripts", "data",
    ])
    def test_does_not_skip_source_dirs(self, dirname: str):
        """Regular source directories should NOT be skipped."""
        assert _should_skip_dir(dirname) is False

    def test_case_sensitive(self):
        """Directory names should be case-sensitive (important on Unix)."""
        assert _should_skip_dir(".git") is True
        assert _should_skip_dir(".Git") is False  # Different case


# ---------------------------------------------------------------------------
# UNIT TESTS: _scan_file()
# ---------------------------------------------------------------------------

class TestScanFile:
    """Test scanning individual files for secrets."""

    def test_finds_secret_in_file(self, tmp_path: Path):
        """A file with a secret should produce a Finding."""
        file_path = write_file(tmp_path, "config.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = _scan_file(file_path)

        assert len(findings) == 1
        assert findings[0].rule.id == "aws-access-key"
        assert findings[0].file == file_path
        assert findings[0].line_no == 1

    def test_returns_empty_list_for_clean_file(self, tmp_path: Path):
        """A clean file should produce an empty list."""
        file_path = write_file(tmp_path, "hello.py", 'print("Hello")\n')

        findings = _scan_file(file_path)

        assert findings == []

    def test_finds_multiple_secrets_in_file(self, tmp_path: Path):
        """Multiple secrets in different lines should all be found."""
        content = (
            'aws = "AKIAIOSFODNN7EXAMPLE"\n'
            'github = "ghp_' + 'A' * 36 + '"\n'
        )
        file_path = write_file(tmp_path, "secrets.env", content)

        findings = _scan_file(file_path)

        assert len(findings) == 2
        assert findings[0].line_no == 1
        assert findings[1].line_no == 2

    def test_line_content_preserved(self, tmp_path: Path):
        """The Finding should contain the actual line text (without newline)."""
        content = 'my_secret = "AKIAIOSFODNN7EXAMPLE"  # secret here\n'
        file_path = write_file(tmp_path, "app.py", content)

        findings = _scan_file(file_path)

        assert findings[0].line == 'my_secret = "AKIAIOSFODNN7EXAMPLE"  # secret here'
        assert "\n" not in findings[0].line

    def test_match_text_extracted(self, tmp_path: Path):
        """The Finding should contain exactly the matched text."""
        file_path = write_file(tmp_path, "cfg.py", 'key = "AKIAIOSFODNN7EXAMPLE" and other stuff\n')

        findings = _scan_file(file_path)

        assert findings[0].match == "AKIAIOSFODNN7EXAMPLE"

    def test_handles_invalid_utf8(self, tmp_path: Path):
        """Files with invalid UTF-8 should be silently skipped (no crash)."""
        # Write binary/invalid UTF-8 data
        file_path = tmp_path / "binary.bin"
        file_path.write_bytes(b'\x80\x81\x82\x83')

        # Should not raise an exception
        findings = _scan_file(file_path)

        # Should return empty (can't decode, so no secrets found)
        assert findings == []

    def test_handles_nonexistent_file(self, tmp_path: Path):
        """Attempting to scan a non-existent file should not crash."""
        file_path = tmp_path / "does_not_exist.txt"

        # Should not raise an exception
        findings = _scan_file(file_path)

        # Should return empty
        assert findings == []

    def test_reports_correct_line_numbers(self, tmp_path: Path):
        """Line numbers should be 1-based and accurate."""
        content = (
            "# comment\n"
            "import os\n"
            'secret1 = "AKIAIOSFODNN7EXAMPLE"\n'
            "x = 1\n"
            'secret2 = "AKIAIOSFODNN7EXAMPLE"\n'
        )
        file_path = write_file(tmp_path, "test.py", content)

        findings = _scan_file(file_path)

        assert len(findings) == 2
        assert findings[0].line_no == 3
        assert findings[1].line_no == 5


# ---------------------------------------------------------------------------
# INTEGRATION TESTS: scan_path()
# ---------------------------------------------------------------------------

class TestScanPath:
    """Test scan_path() with directories and multiple files."""

    def test_scans_directory_recursively(self, tmp_path: Path):
        """scan_path() should find secrets in nested subdirectories."""
        # Create nested structure
        (tmp_path / "subdir").mkdir()
        write_file(tmp_path, "root.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')
        write_file(tmp_path / "subdir", "nested.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        assert len(findings) == 2

    def test_scans_single_file(self, tmp_path: Path):
        """Passing a file path (not directory) should scan just that file."""
        file_path = write_file(tmp_path, "config.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(file_path)

        assert len(findings) == 1
        assert findings[0].file == file_path

    def test_skips_ignored_directories(self, tmp_path: Path):
        """Secrets in ignored directories should not be found."""
        # Create .git and .venv directories with secrets
        git_dir = tmp_path / ".git" / "objects"
        git_dir.mkdir(parents=True)
        write_file(git_dir, "secret.txt", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        write_file(venv_dir, "secret.txt", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        assert findings == []

    def test_skips_binary_extensions_in_directory_scan(self, tmp_path: Path):
        """Binary files should be skipped during directory scan."""
        write_file(tmp_path, "image.png", 'key = "AKIAIOSFODNN7EXAMPLE"\n')
        write_file(tmp_path, "archive.zip", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        assert findings == []

    def test_empty_directory(self, tmp_path: Path):
        """Scanning an empty directory should return no findings."""
        findings = scan_path(tmp_path)

        assert findings == []

    def test_multiple_files_multiple_secrets(self, tmp_path: Path):
        """Should handle many files with many secrets."""
        token = "ghp_" + "X" * 36
        write_file(tmp_path, "file1.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')
        write_file(tmp_path, "file2.sh", f'token = "{token}"\n')
        write_file(tmp_path, "file3.env", 'key2 = "AKIAIOSFODNN7EXAMPLE"\n' + f'token2 = "{token}"\n')

        findings = scan_path(tmp_path)

        assert len(findings) == 4

    def test_different_rule_types(self, tmp_path: Path):
        """Should detect different types of secrets."""
        content = (
            'aws_key = "AKIAIOSFODNN7EXAMPLE"\n'
            f'github = "ghp_' + 'Z' * 36 + '"\n'
        )
        write_file(tmp_path, "creds.py", content)

        findings = scan_path(tmp_path)
        rule_ids = {f.rule.id for f in findings}

        assert "aws-access-key" in rule_ids
        assert "github-pat-classic" in rule_ids

    def test_finding_structure_complete(self, tmp_path: Path):
        """All fields of Finding should be populated correctly."""
        write_file(tmp_path, "test.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        finding = findings[0]
        assert finding.rule is not None
        assert finding.rule.id == "aws-access-key"
        assert finding.file is not None
        assert finding.line_no == 1
        assert finding.line == 'key = "AKIAIOSFODNN7EXAMPLE"'
        assert finding.match == "AKIAIOSFODNN7EXAMPLE"


# ---------------------------------------------------------------------------
# INTEGRATION TESTS: Legacy (existing tests, organized)
# ---------------------------------------------------------------------------

class TestScanPathIntegration:
    """Additional integration tests for scan_path()."""

    def test_scan_finds_aws_key(self, tmp_path: Path):
        """Scanner should detect an AWS Access Key ID in a Python file."""
        write_file(tmp_path, "config.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        # There should be exactly one finding.
        assert len(findings) == 1
        assert findings[0].rule.id == "aws-access-key"
        assert findings[0].line_no == 1

    def test_scan_finds_github_token(self, tmp_path: Path):
        """Scanner should detect a GitHub classic PAT."""
        token = "ghp_" + "Z" * 36
        write_file(tmp_path, "deploy.sh", f'export GH_TOKEN="{token}"\n')

        findings = scan_path(tmp_path)

        assert len(findings) == 1
        assert findings[0].rule.id == "github-pat-classic"

    def test_scan_clean_file_returns_no_findings(self, tmp_path: Path):
        """A file with no secrets should produce zero findings."""
        write_file(tmp_path, "hello.py", 'print("Hello, world!")\n')

        findings = scan_path(tmp_path)

        assert findings == []

    def test_scan_multiple_secrets_in_one_file(self, tmp_path: Path):
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

    def test_scan_skips_binary_extension(self, tmp_path: Path):
        """Files with binary extensions (e.g. .png) should be skipped entirely."""
        # Even though the content looks like a secret, the file has a .png extension.
        write_file(tmp_path, "image.png", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        assert findings == []

    def test_scan_skips_venv_directory(self, tmp_path: Path):
        """The scanner should not descend into virtual-environment directories."""
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        write_file(venv_dir, "site.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(tmp_path)

        assert findings == []

    def test_scan_single_file(self, tmp_path: Path):
        """Passing a single file path (not a directory) should work correctly."""
        file_path = write_file(tmp_path, "creds.py", 'key = "AKIAIOSFODNN7EXAMPLE"\n')

        findings = scan_path(file_path)  # pass the FILE, not the directory

        assert len(findings) == 1

    def test_scan_reports_correct_line_number(self, tmp_path: Path):
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
