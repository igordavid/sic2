# Mocking Strategies for Python Tests

Mocking helps isolate code under test by replacing external dependencies. This guide covers practical strategies.

## When to Mock

**Mock these:**
- External APIs (HTTP calls)
- Database operations
- File system operations
- System calls
- Long-running operations
- Non-deterministic functions (time.now(), random)

**Don't mock these:**
- Internal function calls (unless testing integration)
- Core business logic
- The code you're testing

## Basic Mocking

### Mock Objects

Create a simple mock:

```python
from unittest.mock import Mock

def test_with_mock():
    mock_logger = Mock()
    mock_logger.debug("message")
    
    mock_logger.debug.assert_called_once_with("message")
```

Mock with return value:

```python
mock_api = Mock(return_value="success")
result = mock_api()
assert result == "success"
```

Mock that raises exception:

```python
mock_api = Mock(side_effect=ConnectionError("Network down"))

with pytest.raises(ConnectionError):
    mock_api()
```

## Patching

Replace functions/classes with mocks using `@patch`:

```python
from unittest.mock import patch

@patch("requests.get")
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": "ok"}
    
    import requests
    response = requests.get("http://api.example.com")
    
    assert response.json()["status"] == "ok"
    mock_get.assert_called_once()
```

Context manager syntax:

```python
def test_api_call():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"data": "mocked"}
        
        import requests
        response = requests.get("http://api.example.com")
        assert response.json()["data"] == "mocked"
```

## MagicMock

MagicMock auto-creates attributes and return values:

```python
from unittest.mock import MagicMock

mock_db = MagicMock()
mock_db.query().filter().first.return_value = {"id": 1}

result = mock_db.query().filter().first()
assert result["id"] == 1
```

## Assertion Methods

Verify how mocks were used:

| Method | Purpose |
|--------|---------|
| `assert_called()` | Called at least once |
| `assert_called_once()` | Called exactly once |
| `assert_called_with(*args, **kwargs)` | Called with specific args |
| `assert_called_once_with(*args, **kwargs)` | Called once with specific args |
| `assert_not_called()` | Never called |
| `assert_any_call(*args, **kwargs)` | Called with these args at some point |
| `assert_has_calls(calls)` | Called with this sequence |

```python
mock = Mock()
mock(1, 2, x=3)

mock.assert_called_once_with(1, 2, x=3)
mock.assert_called_with(1, 2, x=3)  # also passes
```

## Patching Different Targets

**Patch module function:**
```python
@patch("mymodule.calculate")
def test_with_calculation(mock_calc):
    mock_calc.return_value = 42
    # your code
```

**Patch class method:**
```python
@patch("mymodule.MyClass.method")
def test_class_method(mock_method):
    mock_method.return_value = "result"
```

**Patch class instantiation:**
```python
@patch("mymodule.MyClass")
def test_class_init(mock_class):
    mock_instance = MagicMock()
    mock_class.return_value = mock_instance
    # Now MyClass() returns mock_instance
```

## Spy vs Mock

**Spy:** Wrap real function, track calls but execute real code
```python
from unittest.mock import patch, call

@patch("mymodule.expensive_operation", wraps=mymodule.expensive_operation)
def test_spy(mock_expensive):
    result = mymodule.expensive_operation(5)
    
    # Real function was called and executed
    assert result == 10
    mock_expensive.assert_called_once_with(5)
```

**Mock:** Replace function, don't execute real code
```python
@patch("mymodule.expensive_operation", return_value=10)
def test_mock(mock_expensive):
    result = mymodule.expensive_operation(5)
    
    # Real function was NOT called
    assert result == 10
```

## Mocking with Fixtures

Combine mocks and fixtures:

```python
@pytest.fixture
def mocked_api():
    with patch("requests.get") as mock:
        mock.return_value.json.return_value = {"success": True}
        yield mock

def test_with_mocked_api(mocked_api):
    import requests
    response = requests.get("http://api.example.com")
    assert response.json()["success"] is True
    mocked_api.assert_called_once()
```

## Common Patterns

### Mock Third-Party Library

```python
@patch("external_lib.fetch_data")
def test_with_external_lib(mock_fetch):
    mock_fetch.return_value = [1, 2, 3, 4, 5]
    
    result = my_function_using_external_lib()
    assert len(result) == 5
```

### Mock Environment Variables

```python
def test_with_env(monkeypatch):
    """monkeypatch is a built-in pytest fixture."""
    monkeypatch.setenv("API_KEY", "test-key-123")
    monkeypatch.setenv("DEBUG", "1")
    
    assert os.getenv("API_KEY") == "test-key-123"
    # Auto-reverted after test
```

### Mock System Time

```python
from unittest.mock import patch
from datetime import datetime

@patch("datetime.datetime")
def test_with_time(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
    
    result = get_current_timestamp()
    assert result.year == 2024
```

### Mock File Operations

```python
from unittest.mock import mock_open, patch

@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_file_read(mock_file):
    with open("any_file.txt") as f:
        content = f.read()
    
    assert content == "file content"
    mock_file.assert_called_once_with("any_file.txt")
```

### Mock Class Initialization

```python
@patch("mymodule.Database")
def test_database_usage(mock_db_class):
    mock_instance = MagicMock()
    mock_db_class.return_value = mock_instance
    mock_instance.query.return_value = [1, 2, 3]
    
    db = Database()
    result = db.query("SELECT *")
    
    assert result == [1, 2, 3]
    mock_instance.query.assert_called_once()
```

### Mock with Side Effects (Multiple Returns)

```python
mock = Mock(side_effect=[1, 2, 3])
assert mock() == 1
assert mock() == 2
assert mock() == 3

with pytest.raises(StopIteration):
    mock()  # 4th call
```

### Mock with Callable Side Effect

```python
def side_effect_fn(*args, **kwargs):
    return args[0] * 2

mock = Mock(side_effect=side_effect_fn)
assert mock(5) == 10
```

## Partial Mocking (Mock Some Methods)

```python
class MyClass:
    def method_a(self):
        return "a"
    
    def method_b(self):
        return "b"

mock_obj = MyClass()
mock_obj.method_a = Mock(return_value="mocked_a")

assert mock_obj.method_a() == "mocked_a"
assert mock_obj.method_b() == "b"  # Not mocked
```

## Resetting Mocks

Reset call count and attributes:

```python
mock = Mock()
mock()
assert mock.call_count == 1

mock.reset_mock()
assert mock.call_count == 0
```

## Common Pitfalls

### Pitfall 1: Wrong Patch Target

```python
# WRONG: patch where imported
from mymodule import function
mock.patch("mymodule.function")  # Doesn't work

# CORRECT: patch where used
import mymodule
@patch("mymodule.function")
def test(mock_func):
    pass
```

### Pitfall 2: Forgetting Side Effects

```python
# WRONG: Mock doesn't raise exception
mock = Mock(side_effect=ValueError("Error"))
with pytest.raises(ValueError):
    mock()  # Passes

# CORRECT
@patch("some_module.some_func", side_effect=ValueError("Error"))
def test(mock_func):
    with pytest.raises(ValueError):
        mock_func()
```

### Pitfall 3: Over-Mocking

```python
# WRONG: Mock too much, lose test value
@patch("datetime.datetime")
@patch("requests.get")
@patch("json.loads")
def test_my_function(mock1, mock2, mock3):
    pass  # No real logic tested

# BETTER: Mock only external dependencies
@patch("requests.get")
def test_my_function(mock_get):
    pass  # Still test core logic
```

## Testing Mock Calls

```python
mock = Mock()
mock(1, 2)
mock(3, 4)

# Check call history
assert mock.call_count == 2
assert mock.call_args == ((3, 4), {})
assert mock.call_args_list == [call(1, 2), call(3, 4)]

# Verify specific call
from unittest.mock import call
mock.assert_has_calls([call(1, 2), call(3, 4)])
```

## Nested Mocking

```python
@patch("module.level2")
@patch("module.level1")
def test_nested(mock_level1, mock_level2):
    # Note: decorators apply bottom-to-top
    # So level1 is second parameter, level2 is first
    pass
```
