"""
Example test file showing pytest patterns and best practices.

This file demonstrates:
- Basic assertions
- Fixtures
- Parametrization
- Exception testing
- Mocking
- Markers
- Test organization with classes
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# ============================================================================
# BASIC TESTS (Simple assertions)
# ============================================================================

class TestBasicAssertions:
    """Group related tests using a class."""

    def test_addition(self):
        """Test basic arithmetic."""
        result = 2 + 2
        assert result == 4

    def test_string_contains(self):
        """Test string operations."""
        text = "hello world"
        assert "world" in text
        assert text.startswith("hello")

    def test_list_operations(self):
        """Test list operations."""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert 3 in items
        assert items[0] == 1


# ============================================================================
# TESTS WITH FIXTURES (Reusing setup)
# ============================================================================

class TestWithFixtures:
    """Demonstrate fixture usage."""

    def test_with_temp_dir(self, temp_dir):
        """Use temp_dir fixture from conftest.py."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_with_sample_data(self, sample_data_list):
        """Use sample_data_list fixture."""
        assert len(sample_data_list) == 3
        assert sample_data_list[0]["name"] == "Alice"

    def test_with_sample_file(self, sample_file):
        """Use sample_file fixture (depends on base_path)."""
        content = sample_file.read_text()
        assert "Sample content" in content
        assert content.count("\n") == 2


# ============================================================================
# PARAMETRIZED TESTS (Same test, multiple inputs)
# ============================================================================

class TestParametrization:
    """Test the same logic with different inputs."""

    @pytest.mark.parametrize("input_value,expected", [
        (2, 4),      # 2 * 2 = 4
        (5, 10),     # 5 * 2 = 10
        (0, 0),      # 0 * 2 = 0
        (-3, -6),    # -3 * 2 = -6
    ])
    def test_multiply_by_two(self, input_value, expected):
        """This test runs 4 times (once per parameter set)."""
        def multiply_by_two(x):
            return x * 2

        assert multiply_by_two(input_value) == expected

    @pytest.mark.parametrize("path_string", [
        "path/to/file.txt",
        "relative/path.py",
        "single.md",
    ])
    def test_path_extensions(self, path_string):
        """Test multiple file paths."""
        path = Path(path_string)
        assert path.suffix in [".txt", ".py", ".md"]

    @pytest.mark.parametrize("format_type,extension", [
        ("json", ".json"),
        ("yaml", ".yaml"),
        ("csv", ".csv"),
    ])
    def test_file_formats(self, format_type, extension):
        """Multiple parameters can be tested together."""
        assert format_type in ["json", "yaml", "csv"]
        assert extension.startswith(".")


# ============================================================================
# EXCEPTION TESTING (Verify error conditions)
# ============================================================================

class TestExceptions:
    """Test that functions raise appropriate exceptions."""

    def test_division_by_zero(self):
        """Verify that division by zero raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            1 / 0

    def test_value_error_with_message(self):
        """Verify exception message."""
        with pytest.raises(ValueError, match="invalid literal"):
            int("not a number")

    def test_file_not_found(self):
        """Verify FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            with open("/nonexistent/path/file.txt", "r"):
                pass

    def test_custom_exception(self):
        """Test custom exceptions."""
        class CustomError(Exception):
            pass

        def raise_custom():
            raise CustomError("Something went wrong")

        with pytest.raises(CustomError, match="Something went wrong"):
            raise_custom()


# ============================================================================
# MOCKING TESTS (Replace external dependencies)
# ============================================================================

class TestMocking:
    """Demonstrate mocking external dependencies."""

    def test_mock_function(self):
        """Mock a function and verify it was called."""
        mock_function = Mock(return_value=42)
        result = mock_function()

        assert result == 42
        mock_function.assert_called_once()

    def test_mock_with_side_effect(self):
        """Mock that raises an exception."""
        mock_function = Mock(side_effect=ValueError("Mocked error"))

        with pytest.raises(ValueError, match="Mocked error"):
            mock_function()

    @patch("builtins.open")
    def test_patch_builtin(self, mock_open):
        """Patch a built-in function."""
        mock_open.return_value.read.return_value = "mocked file content"

        # This would normally read a real file
        with open("any_file.txt") as f:
            content = f.read()

        assert content == "mocked file content"
        mock_open.assert_called_once_with("any_file.txt")

    @patch("requests.get")
    def test_mock_external_api(self, mock_get):
        """Mock an external API call."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "success"}

        # Simulate API call
        import requests
        response = requests.get("https://api.example.com")

        assert response.status_code == 200
        assert response.json()["data"] == "success"

    def test_magic_mock_attributes(self):
        """MagicMock auto-creates attributes and methods."""
        mock_obj = MagicMock()
        mock_obj.method().return_value = "result"

        result = mock_obj.method()
        assert result == "result"
        mock_obj.method.assert_called_once()


# ============================================================================
# FIXTURE WITH PARAMETRIZATION (Fixtures that provide multiple values)
# ============================================================================

class TestFixtureParametrization:
    """Use fixtures that yield multiple values."""

    def test_with_parametrized_fixture(self, config_format):
        """config_format comes from conftest.py with params."""
        assert config_format in ["json", "yaml", "toml"]

    @pytest.mark.parametrize("level", ["debug", "info", "warning"])
    def test_with_log_level_and_format(self, level, config_format):
        """Combine fixture and parametrize (test runs 3×3=9 times)."""
        assert level in ["debug", "info", "warning"]
        assert config_format in ["json", "yaml", "toml"]


# ============================================================================
# MARKERS (Tag tests for selective running)
# ============================================================================

class TestMarkers:
    """Use markers to categorize tests."""

    @pytest.mark.unit
    def test_unit_test(self):
        """This is a fast unit test."""
        assert True

    @pytest.mark.integration
    def test_integration_test(self):
        """This is a slower integration test."""
        assert True

    @pytest.mark.slow
    def test_slow_operation(self):
        """This test takes a long time to run."""
        assert True

    @pytest.mark.skip(reason="Not implemented yet")
    def test_skip_this(self):
        """This test will be skipped."""
        assert False

    @pytest.mark.skipif(True, reason="Always skip")
    def test_conditional_skip(self):
        """Conditionally skip based on runtime checks."""
        assert False


# ============================================================================
# EDGE CASES & REAL-WORLD SCENARIOS
# ============================================================================

class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_empty_list(self):
        """Test with empty input."""
        items = []
        assert len(items) == 0
        assert all(item > 0 for item in items) is True  # vacuously true

    def test_none_value(self):
        """Test with None."""
        value = None
        assert value is None
        assert not value  # None is falsy

    def test_large_number(self):
        """Test with extreme values."""
        big_number = 10**100
        assert big_number > 0
        assert str(big_number).startswith("1")

    def test_unicode_strings(self):
        """Test with Unicode characters."""
        text = "Hello 🌍 World"
        assert "🌍" in text
        assert len(text) == 13


# ============================================================================
# RUNNING THESE TESTS
# ============================================================================

# Command line examples:
#
# Run all tests:
#   pytest
#
# Run only unit tests:
#   pytest -m unit
#
# Run only fast tests (not slow):
#   pytest -m "not slow"
#
# Run with verbose output:
#   pytest -v
#
# Run specific test:
#   pytest test_example.py::TestBasicAssertions::test_addition
#
# Show print statements:
#   pytest -s
#
# Stop on first failure:
#   pytest -x
