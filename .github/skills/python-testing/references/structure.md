# Test Suite Structure and Organization

How to organize tests in growing projects to maintain clarity and minimize maintenance burden.

## Directory Structure

### Small Projects (< 10 test files)

```
project/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_scanner.py
│   ├── test_rules.py
│   ├── test_reporter.py
│   └── __init__.py
└── src/
    └── myproject/
        ├── scanner.py
        ├── rules.py
        └── reporter.py
```

### Medium Projects (10-50 test files)

Mirror source structure in tests/:

```
project/
├── tests/
│   ├── conftest.py              # Global fixtures
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_rules.py
│   ├── api/                     # Organize by domain
│   │   ├── conftest.py          # API-specific fixtures
│   │   ├── test_routes.py
│   │   └── test_models.py
│   └── integration/             # Integration tests
│       ├── conftest.py
│       └── test_end_to_end.py
└── src/
    └── myproject/
        ├── scanner.py
        ├── rules.py
        └── api/
            ├── routes.py
            └── models.py
```

### Large Projects (50+ test files)

Separate by test type and domain:

```
project/
├── tests/
│   ├── conftest.py              # Global shared state
│   ├── __init__.py
│   ├── unit/                    # Fast unit tests
│   │   ├── conftest.py
│   │   ├── test_scanner.py
│   │   ├── test_rules.py
│   │   └── api/
│   │       ├── test_routes.py
│   │       └── test_models.py
│   ├── integration/             # Slower integration tests
│   │   ├── conftest.py          # DB fixtures, mocked services
│   │   └── test_database.py
│   ├── fixtures/                # Reusable fixtures
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── api_mocks.py
│   │   └── sample_data.py
│   └── e2e/                     # End-to-end tests
│       ├── conftest.py
│       └── test_workflows.py
└── src/
    └── myproject/
        ├── scanner.py
        ├── api/
        │   ├── routes.py
        │   └── models.py
        └── database.py
```

## File Naming Conventions

| Pattern | Used For |
|---------|----------|
| `test_*.py` | Standard test files (pytest default) |
| `*_test.py` | Alternative convention |
| `conftest.py` | Shared fixtures (auto-discovered) |
| `__init__.py` | Make test directories packages |

Test function naming:

```python
# Bad: vague names
def test_1():
    pass

def test_stuff():
    pass

# Good: clear, specific names
def test_scanner_skips_binary_files():
    pass

def test_rules_aws_pattern_matches_valid_key():
    pass

def test_reporter_json_includes_severity():
    pass

# Class-based: group related tests
class TestScanner:
    def test_empty_directory(self):
        pass
    
    def test_large_files(self):
        pass

class TestRules:
    def test_aws_key_detection(self):
        pass
    
    def test_github_token_detection(self):
        pass
```

## Fixture Organization

### Centralized Fixtures (conftest.py)

```
tests/
├── conftest.py                  # Global fixtures
│   - temp_dir
│   - sample_config
│   - mock_external_service
├── unit/
│   └── conftest.py              # Unit test-specific
│       - mock_db
│       - mock_cache
└── integration/
    └── conftest.py              # Integration test-specific
        - real_database
        - test_server
```

### Fixture Module Pattern (large projects)

```
tests/
├── fixtures/
│   ├── __init__.py              # Re-export fixtures
│   ├── database.py              # DB-related fixtures
│   │   - db_session
│   │   - db_with_data
│   ├── api_mocks.py             # API mocking fixtures
│   │   - mock_github_api
│   │   - mock_external_service
│   └── sample_data.py           # Test data generators
│       - sample_user
│       - sample_config
└── conftest.py
    # Import and expose fixtures
    from tests.fixtures.database import *
    from tests.fixtures.api_mocks import *
```

Usage in tests:

```python
# Fixtures are auto-discovered from conftest.py
# or explicitly imported
from tests.fixtures.database import db_session

def test_user_creation(db_session):
    user = db_session.create_user("Alice")
    assert user.name == "Alice"
```

## Test Organization Patterns

### By Test Type

```
tests/
├── unit/                        # Fast, isolated tests
│   ├── test_functions.py
│   └── test_classes.py
├── integration/                 # Multiple components
│   ├── test_database_sync.py
│   └── test_api_with_db.py
├── e2e/                         # Full workflows
│   └── test_user_signup.py
└── performance/                 # Benchmarks (optional)
    └── test_scanning_speed.py
```

### By Domain/Feature

```
tests/
├── scanner/
│   ├── test_file_discovery.py
│   ├── test_regex_matching.py
│   └── test_performance.py
├── reporter/
│   ├── test_text_output.py
│   ├── test_json_output.py
│   └── test_formatting.py
└── cli/
    ├── test_commands.py
    └── test_help_text.py
```

### By Behavior (BDD Style)

```
tests/
├── features/
│   ├── scanning/
│   │   ├── test_scan_single_file.py
│   │   ├── test_scan_directory.py
│   │   └── test_ignore_patterns.py
│   └── reporting/
│       ├── test_report_generation.py
│       └── test_output_formats.py
```

## pytest.ini / pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Markers for test categorization
markers = [
    "unit: fast unit tests",
    "integration: slower integration tests",
    "e2e: end-to-end tests",
    "slow: tests taking >1 second",
    "skip_ci: skip in CI pipelines",
]

# Minimum coverage threshold
[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
fail_under = 80
```

## Running Tests by Organization

```bash
# Run only unit tests
pytest tests/unit/

# Run only fast tests (not slow/integration)
pytest -m "not slow"

# Run specific test class
pytest tests/unit/test_scanner.py::TestFileDiscovery

# Run with coverage by domain
pytest --cov=src.scanner tests/unit/scanner/

# Run tests excluding integration
pytest -m "not integration"

# Run in parallel (requires pytest-xdist)
pytest -n auto --dist=loadgroup
```

## Markers for Test Organization

```python
@pytest.mark.unit
def test_isolated_function():
    pass

@pytest.mark.integration
def test_with_database():
    pass

@pytest.mark.slow
def test_scanning_large_repo():
    pass

@pytest.mark.skip_ci
def test_requires_manual_setup():
    pass

class TestScanner:
    @pytest.mark.unit
    def test_empty_directory(self):
        pass
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_repository(self):
        pass
```

Then run selectively:

```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Exclude slow tests
pytest -m "integration and not slow"
```

## Test Data Organization

### Option 1: Data in Fixtures

```python
# conftest.py
@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Alice", "email": "alice@example.com"}

@pytest.fixture
def sample_findings():
    return [
        {"file": "config.py", "rule": "aws-key"},
        {"file": "secrets.env", "rule": "api-key"},
    ]
```

### Option 2: Data Files (fixtures directory)

```
tests/fixtures/
├── sample_data/
│   ├── users.json
│   ├── config.yaml
│   └── large_repo/
│       ├── scanner.py
│       ├── config.py
│       └── secrets.env
```

Load in tests:

```python
def test_with_data_file():
    with open("tests/fixtures/sample_data/users.json") as f:
        users = json.load(f)
    assert len(users) > 0
```

### Option 3: Test Data Builder (Factories)

```python
@pytest.fixture
def user_factory():
    def _create(name="Alice", email="alice@example.com"):
        return {"name": name, "email": email}
    return _create

def test_user_creation(user_factory):
    user1 = user_factory()
    user2 = user_factory(name="Bob")
    assert user1["name"] == "Alice"
    assert user2["name"] == "Bob"
```

## Test Isolation Best Practices

1. **No test dependencies**: Each test should pass independently
   ```python
   # BAD: tests depend on each other
   test_create_user()  # must run first
   test_list_users()   # depends on above
   
   # GOOD: each test is independent
   test_list_empty_users()
   test_list_users_with_data(users_fixture)
   ```

2. **Use fixtures for setup**: Not test methods
   ```python
   # BAD: setup in base class
   class TestBase:
       def setup_method(self):
           self.data = expensive_setup()
   
   # GOOD: use fixtures
   @pytest.fixture
   def data():
       return expensive_setup()
   ```

3. **Clean up after tests**: Especially with real resources
   ```python
   @pytest.fixture
   def database():
       db = create_database()
       yield db
       db.drop_tables()  # cleanup
   ```

## Coverage Organization

Track coverage by test category:

```bash
# Coverage by test type
pytest tests/unit --cov=src --cov-report=html
pytest tests/integration --cov=src --cov-report=html

# Generate combined report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

View results by module:

```
src/scanner.py: 95%      ✓
src/rules.py:   87%      ✓
src/reporter.py: 75%     ⚠ Need more tests
src/cli.py:     60%      ⚠ Needs improvement
```

## CI/CD Integration

Run different test suites at different stages:

```yaml
# .github/workflows/tests.yml
jobs:
  fast-tests:
    steps:
      - run: pytest tests/unit -m "not slow"
  
  full-tests:
    steps:
      - run: pytest tests/ --cov=src
```
