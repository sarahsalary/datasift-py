# datasift-py

**Zero-dependency data conversion, querying, manipulation, streaming, and schema validation for Python.**

[![PyPI version](https://img.shields.io/pypi/v/datasift-py.svg)](https://pypi.org/project/datasift-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/datasift-py.svg)](https://pypi.org/project/datasift-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/sarahsalary/datasift-py/actions/workflows/ci.yml/badge.svg)](https://github.com/sarahsalary/datasift-py/actions/workflows/ci.yml)

## Why datasift-py?

`datasift-py` is a small, dependency-free Python library for working with structured data.

It combines:

- a fluent in-memory API;
- a small query language for nested data;
- CSV and JSONL streaming;
- schema validation using Python type hints;
- conversion between JSON, YAML, TOML, CSV, XML, and JSONL;
- a CLI built on the same library API.

Runtime dependencies are limited to Python's standard library.

## Installation

```bash
pip install datasift-py
```

For development:

```bash
git clone https://github.com/sarahsalary/datasift-py.git
cd datasift-py
python -m pip install -e ".[dev]"
pytest
```

## Quick start

### Fluent API

```python
from datasift import Data

result = (
    Data("users.json")
    .filter(age__gt=30)
    .select("name", "email")
    .sort("-age")
)

result.to("adults.csv")
```

For in-memory data:

```python
from datasift import Data

users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Carol", "age": 40},
]

adults = Data(users).filter(age__gte=30).to_list()
```

### Streaming large files

`Stream` is single-use and lazy. It is intended for CSV and JSONL workloads that should not be fully materialized in memory.

```python
from datasift import Stream

(
    Stream.from_csv("huge.csv")
    .filter(age__gt=30)
    .select("name", "email")
    .to_csv("filtered.csv")
)
```

CSV values remain strings when read. Numeric comparisons such as `age__gt=30` normalize the compared value without changing the original record.

### Query language

```python
from datasift import query

data = {
    "users": [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": False},
        {"name": "Carol", "age": 40, "active": True},
    ]
}

query(data, "users[?age > 30].name")
# ["Carol"]

query(data, "users[?active == true].name")
# ["Alice", "Carol"]

query(data, "users[0].name")
# "Alice"
```

Supported operators include:

- `==`, `!=`, `>`, `>=`, `<`, `<=`
- `&&` and `||`
- dotted paths
- numeric indexes such as `[0]`
- list filters such as `[?age > 30]`
- list expansion with `[*]`

### Schema validation

```python
from typing import List, TypedDict
from datasift import Data

class User(TypedDict):
    name: str
    age: int
    email: str

Data("users.json").expect(List[User]).to("validated.yaml")
```

Validation supports common Python typing constructs including `TypedDict`, `List`, `Dict`, `Tuple`, `Set`, `Optional`, `Union`, and `Literal`.

## Supported formats

| Format | Read | Write | Streaming |
|---|---:|---:|---:|
| JSON | Yes | Yes | No |
| YAML | Yes | Yes | No |
| TOML | Yes | Yes | No |
| CSV | Yes | Yes | Yes |
| XML | Yes | Yes | No |
| JSONL / NDJSON | Yes | Yes | Yes |

YAML uses a small standard-library-compatible subset implemented by the project; it is not intended to be a full YAML 1.2 implementation.

## XML model

XML uses a predictable mapping:

```xml
<users>
  <user id="1">
    <name>Alice</name>
  </user>
</users>
```

becomes:

```python
{
    "users": {
        "user": {
            "@id": 1,
            "name": "Alice",
        }
    }
}
```

Attributes use `@name`, mixed text uses `#text`, and repeated child tags become lists.

When serializing a top-level list, pass an explicit root tag:

```python
Data(users).to_xml(root_tag="users")
```

## CLI

Examples:

```bash
datasift convert users.json users.csv
datasift query users.json 'users[?age > 30].name'
datasift validate users.json --schema schema.py:User
```

Run:

```bash
datasift --help
```

for the complete command set.

## Documentation

The documentation source is in `docs/`.

Build it locally with:

```bash
python -m pip install -e ".[docs]"
mkdocs serve
```

## Development

Useful commands:

```bash
pytest
ruff check .
ruff format --check .
mypy
```

The CI workflow runs the supported Python versions and the project's quality checks.

## Project structure

```text
src/datasift/
├── core.py
├── data.py
├── stream.py
├── query.py
├── schema.py
├── schema_loader.py
├── cli.py
└── formats/
    ├── csv_io.py
    ├── json_io.py
    ├── jsonl_io.py
    ├── toml_io.py
    ├── xml_io.py
    └── yaml_io.py
```

## License

MIT. See [LICENSE](LICENSE).
