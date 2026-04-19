"""
Shared pytest configuration and fixtures.

This file is auto-discovered by pytest and runs before any tests.
Define fixtures here that are reused across multiple test files.

Location: tests/conftest.py or ./conftest.py (root)
"""

import pytest
import tempfile
import os
from pathlib import Path


# ============================================================================
# FIXTURE: Temporary Directory
# ============================================================================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file():
    """Provide a temporary file that's cleaned up after the test."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


# ============================================================================
# FIXTURE: Sample Data
# ============================================================================

@pytest.fixture
def sample_config():
    """Common configuration object for multiple tests."""
    return {
        "debug": False,
        "timeout": 30,
        "retries": 3,
        "verbose": True,
    }


@pytest.fixture
def sample_data_list():
    """Sample list for data processing tests."""
    return [
        {"id": 1, "name": "Alice", "score": 95},
        {"id": 2, "name": "Bob", "score": 87},
        {"id": 3, "name": "Charlie", "score": 92},
    ]


# ============================================================================
# FIXTURE: Fixture with Scope (shared across tests)
# ============================================================================

@pytest.fixture(scope="module")
def expensive_resource():
    """
    Set up once per module, not per test (better performance).
    Useful for: database connections, file parsing, slow operations.
    """
    print("Setting up expensive resource...")
    resource = {"connection": "open", "initialized": True}
    yield resource
    print("Cleaning up expensive resource...")
    resource["connection"] = "closed"


# ============================================================================
# FIXTURE: Parametrized Fixture (multiple values)
# ============================================================================

@pytest.fixture(params=["json", "yaml", "toml"])
def config_format(request):
    """
    Run tests multiple times, once for each parameter.
    Useful for: testing multiple formats, OS variations, configurations.
    """
    return request.param


# ============================================================================
# PYTEST HOOKS (Optional: Configure pytest behavior)
# ============================================================================

def pytest_configure(config):
    """
    Custom pytest configuration.
    Runs once at startup before test discovery.
    """
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection.
    Useful for: auto-adding markers, skipping tests conditionally.
    """
    for item in items:
        # Example: auto-mark all tests in tests/ as unit tests
        if "test_" in item.nodeid:
            if "integration" not in item.nodeid:
                item.add_marker(pytest.mark.unit)


# ============================================================================
# FIXTURE: Fixture with Dependency (composition)
# ============================================================================

@pytest.fixture
def base_path(temp_dir):
    """Depend on another fixture (temp_dir)."""
    path = temp_dir / "data"
    path.mkdir()
    return path


@pytest.fixture
def sample_file(base_path):
    """Build on other fixtures."""
    file_path = base_path / "sample.txt"
    file_path.write_text("Sample content\nLine 2\nLine 3")
    return file_path


# ============================================================================
# FIXTURE: Context Manager Fixture (setup/teardown)
# ============================================================================

@pytest.fixture
def mock_environment(monkeypatch):
    """
    Temporarily modify environment variables.
    Note: monkeypatch is a built-in pytest fixture.
    """
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("API_KEY", "test-key-12345")
    yield
    # No explicit cleanup needed (monkeypatch auto-cleans)


# ============================================================================
# FIXTURE: Autouse Fixture (runs automatically for all tests)
# ============================================================================

@pytest.fixture(autouse=True)
def reset_state():
    """
    Automatically reset state before each test.
    Useful for: clearing caches, resetting singletons, cleanup.
    """
    # Setup: runs before test
    yield
    # Teardown: runs after test


# ============================================================================
# Usage in Tests
# ============================================================================

# In your test files, simply reference fixture names as parameters:
#
# def test_example(temp_dir, sample_config):
#     """temp_dir and sample_config are auto-injected."""
#     assert temp_dir.exists()
#     assert sample_config["debug"] is False
#
# def test_parametrized(config_format):
#     """This test runs 3 times: once for json, yaml, toml."""
#     assert config_format in ["json", "yaml", "toml"]
