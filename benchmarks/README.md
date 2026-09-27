# datasift-py

**Python-native fluent API for data conversion, querying, manipulation, and validation. Zero dependencies.**

[![PyPI version](https://img.shields.io/pypi/v/datasift-py.svg)](https://pypi.org/project/datasift-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/datasift-py.svg)](https://pypi.org/project/datasift-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why datasift-py?

| Feature | datasift-py | dataconv | pureyq | python-benedict | yq | dasel |
|---|---|---|---|---|---|---|
| Fluent / chainable API | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Zero dependencies | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Python-native query syntax | ✅ | ❌ | ❌ (jq) | ❌ | ❌ (jq) | ❌ |
| JSON/YAML/TOML/CSV/XML | ✅ | ✅ | ⚠️ (partial) | ✅ | ❌ | ✅ |
| True streaming (CSV/JSONL) | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ |
| Zero-dep schema validation | ✅ | ❌ | ❌ | ⚠️ (pydantic) | ❌ | ❌ |
| CLI + Library | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |

## Installation

```bash
pip install datasift-py
```

## Quick start

```python
from datasift import Data

# Convert JSON to CSV with a fluent chain
(
    Data("users.json")
    .filter(age__gt=30)
    .select("name", "email")
    .to("adults.csv")
)
```

```python
from datasift import Stream

# Stream a 10 GB CSV without loading it into memory
(
    Stream.from_csv("huge.csv")
    .filter(age__gt=30)
    .select("name", "email")
    .to_csv("filtered.csv")
)
```

```python
from typing import List
from typing_extensions import TypedDict
from datasift import Data

class User(TypedDict):
    name: str
    age: int

Data("users.json").expect(List[User]).to("validated.csv")
```

## Format support

| Format | Read | Write | Notes |
|---|---|---|---|
| JSON | ✅ | ✅ | full support |
| YAML | ✅ | ✅ | subset (mappings, lists, scalars) |
| TOML | ✅ | ✅ | full on Python 3.11+; subset otherwise |
| CSV | ✅ | ✅ | dict-based, header inference |
| JSONL | ✅ | ✅ | ideal for streaming |
| XML | ✅ | ✅ | attributes as `@name`, text as `#text` |

## Streaming

For large CSV and JSONL files:

```python
from datasift import Stream

(
    Stream.from_csv("huge.csv")
    .filter(age__gt=30)
    .select("name", "email")
    .to_csv("filtered.csv")
)
```

Streams are single-use. Use `.cache()` if you need to reuse.

## Schema validation

```python
from typing import List
from typing_extensions import TypedDict
from datasift import Data

class User(TypedDict):
    name: str
    age: int

data = Data("users.json")
result = data.validate(List[User])
if not result.ok:
    for error in result:
        print(error)
```

## Query language

```python
from datasift import query

data = {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
query(data, "users[?age > 28].name")  # ["Alice"]
```

## CLI

```bash
datasift convert input.json output.yaml
datasift query data.json "users[0].name"
datasift formats
```

## Development

```bash
git clone https://github.com/sarahsalary/datasift-py.git
cd datasift-py
pip install -e ".[dev]"
pytest
```

## Documentation

Full documentation: https://sarahsalary.github.io/datasift-py/

## License

MIT