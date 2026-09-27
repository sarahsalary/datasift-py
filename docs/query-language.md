# Query Language

datasift-py includes a tiny, dependency-free query language for nested data.

## Syntax

```
users[0].name
users[?age > 30].name
users[?active == true]
config.db.host
tags[*]
items[?price >= 10 && price <= 100]
```

## Operators

| Operator | Meaning |
|---|---|
| `==` | equal |
| `!=` | not equal |
| `>` | greater than |
| `>=` | greater or equal |
| `<` | less than |
| `<=` | less or equal |
| `&&` | logical AND |
| `\|\|` | logical OR |

## Examples

```python
from datasift import query

data = {
    "users": [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": False},
        {"name": "Carol", "age": 40, "active": True},
    ],
    "config": {"db": {"host": "localhost"}},
    "tags": ["a", "b", "c"],
}

query(data, "config.db.host")               # "localhost"
query(data, "users[0].name")                # "Alice"
query(data, "users[?age > 30].name")        # ["Carol"]
query(data, "users[?active == true].name")  # ["Alice", "Carol"]
query(data, "tags[*]")                      # ["a", "b", "c"]
query(data, "users[?age > 20 && age < 35].name")  # ["Alice", "Bob"]
```

## Compiling once, running many times

For performance, compile a query once and reuse it:

```python
from datasift import compile_query

q = compile_query("users[?age > 30].name")
q(data1)  # ["Carol"]
q(data2)  # ...
```