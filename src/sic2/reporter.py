# reporter.py — formats and prints findings to the terminal.
#
# The scanner produces raw Finding objects. This module is responsible for
# turning those objects into human-readable output.
#
# Keeping formatting separate from scanning logic (the "separation of concerns"
# principle) makes it easy to add new output formats (JSON, SARIF, etc.)
# later without touching the scanner.

from __future__ import annotations

import json  # Python's built-in JSON encoder/decoder
import sys   # for sys.exit() and sys.stdout

from sic2.scanner import Finding  # import the data type we'll be formatting


# ---------------------------------------------------------------------------
# Severity colours for terminal output
# ---------------------------------------------------------------------------
# ANSI escape codes are special character sequences that terminals interpret
# as formatting instructions (colours, bold, etc.).
# \033[ starts an escape sequence; the number selects the colour; m ends it.
# \033[0m resets all formatting back to normal.

_SEVERITY_COLOUR: dict[str, str] = {
    "high":   "\033[91m",  # bright red
    "medium": "\033[93m",  # bright yellow
}
_RESET = "\033[0m"
_BOLD  = "\033[1m"


def _colourise(text: str, colour: str) -> str:
    """Wrap *text* in ANSI colour codes."""
    return f"{colour}{text}{_RESET}"


# ---------------------------------------------------------------------------
# Plain-text (human-readable) reporter
# ---------------------------------------------------------------------------

def print_text(findings: list[Finding], *, use_colour: bool = True) -> None:
    """
    Print findings in a readable, grep-friendly text format.

    Each finding is printed as a block like:

        [HIGH] AWS Access Key ID
        File : src/config.py:42
        Match: AKIAIOSFODNN7EXAMPLE
        Line : aws_key = "AKIAIOSFODNN7EXAMPLE"
    """
    if not findings:
        # Nothing found — reassure the user.
        print("No secrets detected.")
        return

    for finding in findings:
        severity = finding.rule.severity.upper()
        colour   = _SEVERITY_COLOUR.get(finding.rule.severity, "") if use_colour else ""

        # Header line: severity badge + rule name
        header = f"[{severity}] {finding.rule.name}"
        print(_colourise(_BOLD + header, colour) if use_colour else header)

        # File path with line number — many editors accept "file:line" syntax
        # so users can click/copy-paste to jump straight to the finding.
        print(f"  File : {finding.file}:{finding.line_no}")
        print(f"  Match: {finding.match}")
        print(f"  Line : {finding.line.strip()}")
        print()  # blank line between findings for readability


# ---------------------------------------------------------------------------
# JSON reporter
# ---------------------------------------------------------------------------

def print_json(findings: list[Finding]) -> None:
    """
    Print findings as a JSON array to stdout.

    JSON output is useful for piping results into other tools or CI systems.
    Each finding becomes a JSON object with all relevant fields.
    """
    # Convert each Finding dataclass into a plain dict that json.dumps() can
    # serialise. (json.dumps() doesn't know how to handle custom classes.)
    output = [
        {
            "rule_id":   finding.rule.id,
            "rule_name": finding.rule.name,
            "severity":  finding.rule.severity,
            "file":      str(finding.file),   # Path objects must be converted to str
            "line_no":   finding.line_no,
            "match":     finding.match,
            "line":      finding.line.strip(),
        }
        for finding in findings
    ]

    # indent=2 makes the JSON human-readable; sort_keys keeps it deterministic.
    print(json.dumps(output, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# Summary / exit-code helper
# ---------------------------------------------------------------------------

def summarise(findings: list[Finding]) -> None:
    """Print a one-line summary and exit with a non-zero code if secrets were found."""
    count = len(findings)
    if count == 0:
        print("Scan complete — no secrets found.")
        sys.exit(0)
    else:
        # Exit code 1 signals "findings present" to CI pipelines, pre-commit
        # hooks, and shell scripts that check `$?`.
        print(f"Scan complete — {count} potential secret(s) found.")
        sys.exit(1)
