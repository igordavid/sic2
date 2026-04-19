# test_rules.py — unit tests for the detection rules in rules.py.
#
# A "unit test" checks a small, isolated piece of behaviour.
# Here we verify that each regex:
#   1. Matches strings that really ARE secrets (true positives).
#   2. Does NOT match strings that are not secrets (no false positives).
#
# Run all tests with:  pytest
# Run just this file: pytest tests/test_rules.py
# Run one test:       pytest tests/test_rules.py::test_aws_access_key_matches -v


# Import the rules we want to test directly so we can call .pattern.search()
from sic2.rules import RULES

# Build a lookup dict so tests can reference rules by ID instead of by index.
# e.g. RULE["aws-access-key"].pattern.search("AKIAIOSFODNN7EXAMPLE")
RULE = {r.id: r for r in RULES}


# ---------------------------------------------------------------------------
# AWS Access Key ID
# ---------------------------------------------------------------------------

def test_aws_access_key_matches():
    """A real-looking AWS key ID should be detected."""
    # AKIA followed by exactly 16 uppercase alphanumeric chars is valid.
    assert RULE["aws-access-key"].pattern.search("AKIAIOSFODNN7EXAMPLE")


def test_aws_access_key_no_match_wrong_prefix():
    """A string that starts with something other than AKIA/ABIA/ACCA/ASIA should not match."""
    assert not RULE["aws-access-key"].pattern.search("XKIAIOSFODNN7EXAMPLE")


def test_aws_access_key_no_match_too_short():
    """Fewer than 16 chars after the prefix should not match."""
    assert not RULE["aws-access-key"].pattern.search("AKIA123SHORT")


# ---------------------------------------------------------------------------
# AWS Secret Access Key
# ---------------------------------------------------------------------------

def test_aws_secret_key_matches():
    """A variable assignment of a 40-char secret key should be detected."""
    line = 'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
    assert RULE["aws-secret-key"].pattern.search(line)


def test_aws_secret_key_no_match_without_variable_name():
    """A standalone 40-char string with no variable name should NOT match.

    This is intentional: we require the variable name to reduce false positives
    from legitimate base64-encoded data.
    """
    assert not RULE["aws-secret-key"].pattern.search("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")


# ---------------------------------------------------------------------------
# GitHub tokens
# ---------------------------------------------------------------------------

def test_github_classic_pat_matches():
    """Classic GitHub PATs start with ghp_ and are 40 chars total."""
    token = "ghp_" + "A" * 36   # ghp_ + 36 chars = valid classic PAT
    assert RULE["github-pat-classic"].pattern.search(token)


def test_github_fine_grained_pat_matches():
    """Fine-grained PATs start with github_pat_ and are much longer."""
    token = "github_pat_" + "B" * 82
    assert RULE["github-pat-fine-grained"].pattern.search(token)


def test_github_oauth_matches():
    """GitHub OAuth tokens start with gho_."""
    token = "gho_" + "C" * 36
    assert RULE["github-oauth"].pattern.search(token)


def test_github_app_token_matches():
    """GitHub App installation tokens start with ghs_."""
    token = "ghs_" + "D" * 36
    assert RULE["github-app-token"].pattern.search(token)


def test_github_classic_pat_no_match_wrong_prefix():
    """A token that starts with ghx_ should not match the classic PAT rule."""
    assert not RULE["github-pat-classic"].pattern.search("ghx_" + "A" * 36)


# ---------------------------------------------------------------------------
# Generic API key
# ---------------------------------------------------------------------------

def test_generic_api_key_matches():
    """A variable named api_key assigned a long string should be detected."""
    assert RULE["generic-api-key"].pattern.search('api_key = "supersecretvalue1234"')


def test_generic_api_key_matches_variations():
    """Different common variable names should all be caught."""
    cases = [
        'APIKEY = "supersecretvalue1234"',
        'api-secret = "supersecretvalue1234"',
        'access_token = "supersecretvalue1234"',
    ]
    for case in cases:
        assert RULE["generic-api-key"].pattern.search(case), f"Should have matched: {case}"


def test_generic_api_key_no_match_too_short():
    """Values shorter than 16 characters should not be flagged.

    Short values are almost certainly placeholder strings, not real secrets.
    """
    assert not RULE["generic-api-key"].pattern.search('api_key = "short"')
