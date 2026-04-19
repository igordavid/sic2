# scanner.py — walks a directory tree and applies rules to each file.
#
# This is the "engine" of sic2. The CLI calls scan_path(), which:
#   1. Walks every file under the given directory (or checks a single file).
#   2. Reads each file's text content line by line.
#   3. Runs every Rule's regex against each line.
#   4. Yields a Finding for every match it finds.
#
# Using `yield` (a Python generator) means results are streamed to the caller
# one at a time rather than collecting everything into memory first — important
# when scanning large repositories.

from __future__ import annotations

import os                          # for walking the directory tree
from dataclasses import dataclass  # lightweight data container
from pathlib import Path           # modern, object-oriented file paths

from sic2.rules import RULES, Rule  # our built-in detection rules


# ---------------------------------------------------------------------------
# Files and directories we never want to scan
# ---------------------------------------------------------------------------
# Scanning binary files or generated artefacts wastes time and produces garbage
# results. We skip them by checking extensions and directory names.

# File extensions that are almost certainly binary or generated.
BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
        ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
        ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyo",
        ".whl", ".egg", ".lock",
    }
)

# Directory names that are almost certainly not hand-written source code.
SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git", ".hg", ".svn",             # version control internals
        "__pycache__", ".mypy_cache",       # Python bytecode / type-checker cache
        "node_modules", ".yarn",            # JavaScript dependencies
        ".venv", "venv", "env", ".env",    # Python virtual environments
        "dist", "build", ".eggs",           # build output
    }
)


@dataclass
class Finding:
    """Represents a single secret detected in a file."""

    rule: Rule       # which rule triggered
    file: Path       # path to the file that contains the secret
    line_no: int     # 1-based line number where the match was found
    line: str        # the raw line text (so the user can see context)
    match: str       # the exact substring that matched the regex


def _should_skip_file(path: Path) -> bool:
    """Return True if we should skip this file entirely."""
    # Skip files whose extension is in our binary/generated list.
    return path.suffix.lower() in BINARY_EXTENSIONS


def _should_skip_dir(name: str) -> bool:
    """Return True if we should skip descending into this directory."""
    return name in SKIP_DIRS


def _scan_file(path: Path) -> list[Finding]:
    """
    Scan a single file and return all findings.

    We read the file line by line so we can report the exact line number.
    If the file cannot be decoded as UTF-8 text we silently skip it —
    it's probably a binary file whose extension we didn't recognise.
    """
    findings: list[Finding] = []

    try:
        # `errors="replace"` substitutes the Unicode replacement character
        # for any byte sequences that aren't valid UTF-8 instead of crashing.
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line_no, line in enumerate(fh, start=1):  # start=1 → 1-based numbering
                for rule in RULES:
                    # re.Pattern.search() scans the whole line for the pattern.
                    # (re.match() would only check the start of the line.)
                    match = rule.pattern.search(line)
                    if match:
                        findings.append(
                            Finding(
                                rule=rule,
                                file=path,
                                line_no=line_no,
                                line=line.rstrip("\n"),  # strip trailing newline for display
                                match=match.group(0),   # group(0) = the full matched text
                            )
                        )
    except OSError:
        # File disappeared between directory listing and open, or permission
        # denied — just skip it.
        pass

    return findings


def scan_path(root: Path) -> list[Finding]:
    """
    Recursively scan *root* (a file or directory) and return all findings.

    If *root* is a file, only that file is scanned.
    If *root* is a directory, the entire tree is walked.
    """
    all_findings: list[Finding] = []

    if root.is_file():
        # Single-file mode: the user pointed us directly at one file.
        all_findings.extend(_scan_file(root))
        return all_findings

    # os.walk() is a generator that yields (current_dir, subdirs, files)
    # for every directory in the tree rooted at `root`.
    for dirpath, dirnames, filenames in os.walk(root):
        # Mutating `dirnames` IN PLACE tells os.walk() not to descend
        # into those subdirectories on the next iteration.
        # We filter out directories we want to skip.
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(d)]

        for filename in filenames:
            file_path = Path(dirpath) / filename  # build the full path
            if _should_skip_file(file_path):
                continue
            all_findings.extend(_scan_file(file_path))

    return all_findings
