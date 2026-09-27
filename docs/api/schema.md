# Schema Validation

Validate data against Python type hints — no pydantic required.

## Quick start

```python
from typing import List, Optional
from typing_extensions import TypedDict
from datasift import Data

class User(TypedDict):
    name: str
    age: int
    email: Optional[str]

data = Data("users.json")

# Validate and get all errors
result = data.validate(List[User])
if not result.ok:
    for error in result:
        print(error)  # $.users[2].age: expected int, got str

# Or validate and raise on first error
data.expect(List[User]).filter(age__gt=30).to("adults.csv")
```

## Supported schemas

- Primitives: `str`, `int`, `float`, `bool`, `type(None)`
- Containers: `list`, `dict`, `tuple`, `set`
- Generics: `List[int]`, `Dict[str, int]`, `Tuple[int, str]`, `Tuple[int, ...]`, `Set[str]`
- Unions: `Union[int, str]`, `Optional[str]`
- Literals: `Literal["a", "b"]`
- `TypedDict` classes (nested supported)
- Plain dict schemas: `{"name": str, "age": int}`

## Error paths

Error paths use JSONPath-style notation:

- `$` — root
- `$.name` — top-level key
- `$[0]` — first list item
- `$[0].address.city` — nested

## Direct API

```python
from datasift import validate, is_valid, validate_or_raise
from datasift.schema import SchemaError, ValidationResult

result = validate(data, List[User])
assert result.ok

if is_valid(data, List[User]):
    print("valid")

validate_or_raise(data, List[User])  # raises SchemaError
```

## Stream validation

```python
from datasift import Stream

# Validate up to 1000 records
result = Stream.from_jsonl("users.jsonl").validate(User, sample=1000)
assert result.ok

# Or raise on first failure
Stream.from_jsonl("users.jsonl").expect(User, sample=1)
```

## Nested TypedDicts

```python
class Address(TypedDict):
    city: str
    zip: str

class Person(TypedDict):
    name: str
    address: Address

data = {
    "name": "Alice",
    "address": {"city": "Tehran", "zip": "12345"},
}

validate(data, Person).ok  # True
```

## Optional fields

```python
class PartialUser(TypedDict, total=False):
    name: str
    age: int

validate({}, PartialUser).ok  # True
validate({"name": "Alice"}, PartialUser).ok  # True
```