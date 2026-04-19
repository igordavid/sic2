---
name: python-testing
description: 'Test Python projects using pytest. Use when: writing unit tests, organizing test suites, creating fixtures, implementing test strategies, increasing coverage, or debugging failing tests.'
argument-hint: 'What testing task? E.g., "write unit tests for scanner.py", "set up fixtures", "improve test coverage"'
---

# Python Testing with pytest

Comprehensive workflow for testing Python projects with pytest, fixtures, mocking, and best practices.

## When to Use

- Writing unit tests for new code
- Setting up test suites in a new project
- Organizing tests (directory structure, naming conventions)
- Creating and managing fixtures for test data
- Implementing mocking for external dependencies
- Measuring and improving test coverage
- Debugging failing tests
- Refactoring tests for maintainability

## Core Concepts

### 1. Test Organization
- **File naming**: `test_*.py` or `*_test.py`
- **Directory layout**: Mirror source structure in `tests/` folder
- **Naming**: `test_<module>_<function>` or `test_<module>_<class>_<method>`
- **Grouping**: Use test classes to organize related tests

### 2. pytest Basics
- **Assertions**: Plain `assert` statements (pytest rewrites them for clarity)
- **Fixtures**: Reusable test setup/teardown with `@pytest.fixture`
- **Parametrization**: Run same test with multiple inputs: `@pytest.mark.parametrize`
- **Markers**: Tag tests with `@pytest.mark.skip`, `.slow`, `.integration`, etc.

### 3. Test Strategies

**Unit Tests**: Test individual functions/methods in isolation
```python
def test_function_returns_correct_value():
    result = my_function(5)
    assert result == 10
```

**Fixtures**: Share setup code across tests
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

**Mocking**: Replace external dependencies
```python
from unittest.mock import patch

def test_with_mock():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"data": "mocked"}
        result = call_external_api()
        assert result["data"] == "mocked"
```

**Parametrization**: Test multiple scenarios
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (5, 10),
    (0, 0),
])
def test_multiple_inputs(input, expected):
    assert my_function(input) == expected
```

## Step-by-Step Workflow

### Phase 1: Setup
1. Install pytest: `pip install pytest`
2. Create `conftest.py` in `tests/` folder (or at repo root)
3. Use [conftest template](./assets/conftest.py) as starting point
4. Create `tests/` directory structure mirroring your source code

### Phase 2: Write Tests
1. Choose a module to test (start small)
2. Create test file: `tests/test_<module>.py`
3. Use [test template](./assets/test_example.py) as reference
4. Write `test_*` functions covering happy paths, edge cases, errors
5. Run tests locally: `pytest -v`

### Phase 3: Add Fixtures
1. Identify common setup (sample data, mocks, db connections)
2. Create fixtures in `conftest.py` or at top of test file
3. Use fixture dependencies for composition
4. Use fixture scopes appropriately: `function` (default), `class`, `module`, `session`

### Phase 4: Improve Coverage
1. Run coverage report: `pytest --cov=src --cov-report=html`
2. Identify untested code paths
3. Add tests for edge cases, error conditions, branches
4. Aim for >80% coverage; prioritize critical paths

### Phase 5: Organize and Maintain
1. Group related tests in classes
2. Use markers for categorization: `@pytest.mark.unit`, `.integration`, `.slow`
3. Refactor fixtures as test base classes when needed
4. Run with `pytest -m "not slow"` for fast iterations

## Commands Reference

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_scanner.py

# Run specific test
pytest tests/test_scanner.py::test_function_name

# Run tests matching pattern
pytest -k "name_contains_this"

# Run with coverage
pytest --cov=src --cov-report=html

# Run excluding certain markers
pytest -m "not slow"

# Run only certain markers
pytest -m unit

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Parallel execution (install pytest-xdist)
pytest -n auto
```

## Templates and Resources

- [conftest.py template](./assets/conftest.py) — Shared fixtures, configuration
- [test_example.py template](./assets/test_example.py) — Example test file structure
- [Fixture patterns](./references/fixtures.md) — Detailed fixture guide
- [Mocking strategies](./references/mocking.md) — When and how to mock dependencies
- [Test structure guide](./references/structure.md) — Organizing large test suites

## Common Patterns

### Fixture with Cleanup
```python
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    yield path
    os.remove(path)  # cleanup
```

### Fixture Dependency
```python
@pytest.fixture
def db(temp_file):  # depends on temp_file fixture
    return Database(temp_file)

def test_query(db):
    result = db.query("SELECT * FROM users")
    assert len(result) > 0
```

### Parametrized Fixture
```python
@pytest.fixture(params=[1, 2, 3])
def number(request):
    return request.param

def test_with_numbers(number):
    # runs 3 times with number = 1, 2, 3
    assert number > 0
```

### Mock Patch
```python
@patch("module.external_function")
def test_with_patch(mock_external):
    mock_external.return_value = "mocked"
    result = my_function()
    mock_external.assert_called_once()
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError" in tests | Ensure `conftest.py` has proper import paths or use pytest plugins like `pytest-pythonpath` |
| Fixture not found | Check spelling; fixtures defined in `conftest.py` or same file are auto-discovered |
| Tests pass locally, fail in CI | Check environment variables, paths, or system differences; use markers for platform-specific tests |
| Tests are slow | Use `@pytest.mark.slow`, run with `-m "not slow"`, or parallelize with pytest-xdist |
| Hard to debug fixture | Use `pytest --fixtures` to list all available fixtures, or add `print()` statements with `-s` flag |

## Next Steps

1. **Choose a module** in your project to test
2. **Use the templates**: Start with [test_example.py](./assets/test_example.py)
3. **Write 5-10 tests** covering the main function/class
4. **Measure coverage**: `pytest --cov`
5. **Iterate**: Add edge cases and error scenarios
6. **Organize**: Graduate to `conftest.py` fixtures once patterns emerge

---

**Need help?** Describe what you're testing: e.g., "write tests for scanner.py", "add mocking for external API", "improve test coverage to 85%"
