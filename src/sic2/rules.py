# rules.py — defines WHAT counts as a secret.
#
# Each Rule pairs a human-readable name with a regular expression (regex).
# A regex is a pattern that the scanner uses to search through text.
# When the pattern matches a piece of code, we flag it as a potential secret.
#
# Adding a new secret type is as simple as appending a new Rule() to RULES.

import re  # Python's built-in regular expression library
from dataclasses import dataclass  # lightweight way to define data-holding classes


@dataclass(frozen=True)
# `frozen=True` makes Rule instances immutable (read-only after creation),
# which prevents accidental modification of rules at runtime.
class Rule:
    """A single detection rule."""

    id: str        # short machine-readable identifier, e.g. "aws-access-key"
    name: str      # human-readable label shown in scan results
    pattern: re.Pattern[str]  # compiled regex — pre-compiled for performance
    severity: str = "high"    # "high" or "medium"; defaults to "high"


# ---------------------------------------------------------------------------
# Built-in rules
# ---------------------------------------------------------------------------
# re.compile() turns a pattern string into a compiled regex object.
# Compiling once here (at import time) is faster than compiling on every match.
#
# Regex quick-reference used below:
#   (?<! )   — negative lookbehind: the match must NOT be preceded by this
#   (?! )    — negative lookahead:  the match must NOT be followed by this
#   (?i)     — case-insensitive flag
#   [A-Z0-9] — character class: any uppercase letter or digit
#   {16}     — exactly 16 of the previous token
#   \s*      — zero or more whitespace characters
#   ['\"]?   — an optional single or double quote
# ---------------------------------------------------------------------------

RULES: list[Rule] = [
    Rule(
        id="aws-access-key",
        name="AWS Access Key ID",
        # AWS access key IDs always start with one of these 4-letter prefixes
        # followed by exactly 16 uppercase alphanumeric characters.
        # The lookbehind/lookahead prevent matching longer strings that merely
        # contain this pattern in the middle.
        pattern=re.compile(r"(?<![A-Z0-9])(AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    ),
    Rule(
        id="aws-secret-key",
        name="AWS Secret Access Key",
        # AWS secret keys are 40-character base64 strings. On their own they
        # look like random noise, so we only flag them when they appear right
        # after a recognisable variable name like `aws_secret_access_key = ...`
        pattern=re.compile(
            r"(?i)(?:aws_secret_access_key|aws_secret_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
        ),
    ),
    Rule(
        id="github-pat-classic",
        name="GitHub Personal Access Token (classic)",
        # GitHub classic PATs always start with the literal prefix "ghp_"
        # followed by 36 alphanumeric characters.
        pattern=re.compile(r"ghp_[A-Za-z0-9]{36}"),
    ),
    Rule(
        id="github-pat-fine-grained",
        name="GitHub Fine-Grained PAT",
        # Fine-grained PATs use the prefix "github_pat_" and are much longer.
        pattern=re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    ),
    Rule(
        id="github-oauth",
        name="GitHub OAuth Token",
        # OAuth app tokens always begin with "gho_".
        pattern=re.compile(r"gho_[A-Za-z0-9]{36}"),
    ),
    Rule(
        id="github-app-token",
        name="GitHub App Installation Token",
        # GitHub App tokens begin with "ghs_".
        pattern=re.compile(r"ghs_[A-Za-z0-9]{36}"),
    ),
    Rule(
        id="generic-api-key",
        name="Generic API Key assignment",
        severity="medium",  # lower confidence — more likely to produce false positives
        # Catches patterns like:
        #   api_key = "abc123..."
        #   API_KEY: "abc123..."
        #   apiSecret = "abc123..."
        # The value must be at least 16 characters to reduce false positives
        # from short placeholder strings like "TODO" or "changeme".
        pattern=re.compile(
            r"(?i)(?:api[_\-]?key|apikey|api[_\-]?secret|access[_\-]?token)\s*[=:]\s*['\"]([A-Za-z0-9\-_.]{16,})['\"]"
        ),
    ),
]
