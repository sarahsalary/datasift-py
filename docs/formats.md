# Formats

datasift-py supports six formats out of the box, with zero dependencies.

| Format | Read | Write | Extension | Notes |
|---|---|---|---|---|
| JSON | ✅ | ✅ | `.json` | full support |
| YAML | ✅ | ✅ | `.yaml`, `.yml` | subset (mappings, lists, scalars) |
| TOML | ✅ | ✅ | `.toml` | full on Python 3.11+; subset otherwise |
| CSV | ✅ | ✅ | `.csv` | dict-based, header inference |
| JSONL | ✅ | ✅ | `.jsonl`, `.ndjson` | ideal for streaming |
| XML | ✅ | ✅ | `.xml` | attributes as `@name`, text as `#text` |

## JSON

Standard `json` module from the Python standard library.

```python
Data({"a": 1}).to("out.json")
Data("in.json").data  # {"a": 1}
```

## YAML

Minimal subset: mappings, sequences, scalars, quoted strings, comments.

```yaml
name: Alice
age: 30
tags:
  - a
  - b
```

For full YAML 1.2, install PyYAML separately.

## TOML

Uses `tomllib` on Python 3.11+; falls back to a minimal parser otherwise.

```toml
title = "Test"
count = 5

[nested]
x = 1
```

## CSV

Dict-based with automatic header inference.

```csv
name,age
Alice,30
Bob,25
```

```python
Data([{"name": "Alice", "age": 30}]).to("out.csv")
```

## JSONL

JSON Lines — one JSON value per line. Ideal for streaming.

```jsonl
{"name": "Alice", "age": 30}
{"name": "Bob", "age": 25}
```

## XML

Convention:

- Root element → `{"root_tag": content}`
- Attributes → `"@name"` keys
- Text content (with attributes/children) → `"#text"`
- Repeated sibling tags → lists
- Scalars are type-inferred

Example:

```xml
<users>
  <user id="1">
    <name>Alice</name>
    <age>30</age>
  </user>
  <user id="2">
    <name>Bob</name>
    <age>25</age>
  </user>
</users>
```

maps to:

```python
{
    "users": {
        "user": [
            {"@id": 1, "name": "Alice", "age": 30},
            {"@id": 2, "name": "Bob", "age": 25},
        ]
    }
}
```

### XML serialization of top-level lists

A top-level Python list requires an explicit root tag:

```python
Data([
    {"name": "Alice"},
    {"name": "Bob"},
]).to_xml(root_tag="users")
```

This produces a `<users>` root with repeated `<user>` children.
