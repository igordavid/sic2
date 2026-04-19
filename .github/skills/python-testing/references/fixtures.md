# Fixture Patterns and Best Practices

Fixtures are the foundation of maintainable pytest suites. This guide covers advanced patterns.

## What is a Fixture?

A fixture is a reusable, composable setup function that:
- Runs before one or more tests
- Provides data or resources to tests
- Cleans up after tests complete
- Can depend on other fixtures

```python
@pytest.fixture
def user():
    """Simple fixture returning data."""
    return {"id": 1, "name": "Alice"}

def test_user(user):
    assert user["name"] == "Alice"
```

## Fixture Scopes

| Scope | Runs | Use Case |
|-------|------|----------|
| `function` (default) | Once per test function | Most common; fresh state each test |
| `class` | Once per test class | Shared data for related tests |
| `module` | Once per test file | Expensive setup (DB, files, network) |
| `session` | Once per test run | Rarely needed; affects test isolation |

```python
@pytest.fixture(scope="session")
def database():
    """Expensive setup, shared across all tests."""
    db = setup_expensive_db()
    yield db
    db.cleanup()
```

## Fixture Composition (Dependency Injection)

Fixtures can depend on other fixtures, creating a composition chain:

```python
@pytest.fixture
def base_path(tmp_path):
    path = tmp_path / "data"
    path.mkdir()
    return path

@pytest.fixture
def config_file(base_path):
    """Depends on base_path."""
    config = base_path / "config.json"
    config.write_text('{"key": "value"}')
    return config

def test_with_nested_fixtures(config_file):
    """Both fixtures are set up automatically."""
    assert config_file.exists()
```

## Cleanup (Setup/Teardown)

Use `yield` to separate setup from teardown:

```python
@pytest.fixture
def temporary_file():
    """Create a file, then delete it."""
    file_path = "/tmp/test_file.txt"
    
    # Setup
    with open(file_path, "w") as f:
        f.write("test content")
    
    # Provide to test
    yield file_path
    
    # Teardown (cleanup)
    os.remove(file_path)
```

With context managers:

```python
@pytest.fixture
def temp_directory():
    """Use context manager for automatic cleanup."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
    # Automatic cleanup when exiting context manager
```

## Parametrized Fixtures

A fixture that returns multiple values; tests run once per value:

```python
@pytest.fixture(params=[1, 2, 3])
def number(request):
    return request.param

def test_number(number):
    # Runs 3 times: number=1, number=2, number=3
    assert number > 0
```

Parametrize with IDs for clearer output:

```python
@pytest.fixture(
    params=[
        ("json", {"data": "value"}),
        ("yaml", {"nested": {"key": "value"}}),
    ],
    ids=["json_format", "yaml_format"]
)
def config(request):
    fmt, data = request.param
    return fmt, data

def test_config(config):
    fmt, data = config
    assert isinstance(data, dict)
```

## Autouse Fixtures

Run automatically without being explicitly requested:

```python
@pytest.fixture(autouse=True)
def reset_cache():
    """Reset cache before each test."""
    cache.clear()
    yield
    cache.clear()

def test_something():
    # cache is auto-reset
    pass
```

## Indirect Parametrization

Pass parametrization to a fixture instead of directly to test:

```python
@pytest.fixture
def user(request):
    """Fixture receives parametrized values."""
    return {"name": request.param, "active": True}

@pytest.mark.parametrize("user", ["Alice", "Bob"], indirect=True)
def test_user_activity(user):
    # user fixture is called 2x with different values
    assert user["active"] is True
```

## Built-in Fixtures

pytest provides useful fixtures:

| Fixture | Purpose |
|---------|---------|
| `tmp_path` | Temp directory (Path object) |
| `tmp_path_factory` | Create multiple temp directories |
| `capsys` | Capture stdout/stderr |
| `caplog` | Capture log messages |
| `monkeypatch` | Mock environment variables, attributes |
| `tmpdir` | Older temp directory (string path) |

```python
def test_with_capsys(capsys):
    """Capture printed output."""
    print("Hello World")
    captured = capsys.readouterr()
    assert "Hello World" in captured.out

def test_with_monkeypatch(monkeypatch):
    """Modify environment temporarily."""
    monkeypatch.setenv("DEBUG", "1")
    assert os.getenv("DEBUG") == "1"
    # Auto-reverted after test

def test_with_caplog(caplog):
    """Capture log output."""
    logging.info("Test message")
    assert "Test message" in caplog.text
```

## Fixture Factory Pattern

Return a callable that creates multiple instances:

```python
@pytest.fixture
def create_user():
    """Factory fixture: returns a function."""
    def _create_user(name, active=True):
        return {"name": name, "active": active}
    return _create_user

def test_with_factory(create_user):
    alice = create_user("Alice")
    bob = create_user("Bob", active=False)
    
    assert alice["name"] == "Alice"
    assert bob["active"] is False
```

## Request Object

Access metadata about the test request:

```python
@pytest.fixture
def request_info(request):
    """Access test metadata."""
    return {
        "name": request.node.name,      # test function name
        "module": request.module.__name__,
        "config": request.config,
        "scope": request.scope,
    }
```

## Fixture Naming

**Good names:**
- `user_fixture` — clear what it provides
- `temp_config_file` — describes what's created
- `mocked_api` — indicates it's mocked
- `sample_data` — indicates test data

**Avoid:**
- `setup` — too generic
- `obj` — unclear what it is
- `x` — no context

## Organization

**Small projects:** Put all fixtures in `conftest.py`

**Large projects:** Create fixture modules:
```
tests/
├── conftest.py                # General fixtures
├── fixtures/
│   ├── __init__.py
│   ├── database.py            # DB-related fixtures
│   ├── api.py                 # API-related fixtures
│   └── files.py               # File-related fixtures
```

Import in tests:
```python
from tests.fixtures.database import db_session
from tests.fixtures.api import mock_api

def test_something(db_session, mock_api):
    pass
```

## Common Patterns

**Pattern: Skip certain tests**
```python
@pytest.fixture
def requires_postgres(request):
    if "postgres" not in os.getenv("DB", ""):
        request.applymarker(pytest.mark.skip(reason="Requires PostgreSQL"))

def test_postgres_specific(requires_postgres):
    pass
```

**Pattern: Fixture with optional cleanup**
```python
@pytest.fixture
def database(request):
    db = setup_db()
    yield db
    if request.config.getoption("--keep-db"):
        print(f"Database left at {db.path}")
    else:
        db.cleanup()
```

**Pattern: Cached fixture**
```python
@pytest.fixture(scope="session")
def large_dataset(tmp_path_factory):
    """Load once, cache for entire session."""
    cache_dir = tmp_path_factory.mktemp("cache")
    data = load_or_compute_large_data(cache_dir)
    return data
```
