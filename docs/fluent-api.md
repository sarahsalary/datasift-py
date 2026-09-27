# Fluent API

The `Data` class provides a chainable, Python-native interface for data manipulation.

## Loading data

```python
from datasift import Data

data = Data("users.json")
data = Data({"name": "Alice"})          # in-memory
data = Data("users.csv")
data = Data("users.yaml")
data = Data("users.xml")
data = Data("users.jsonl")
```

## Filtering

```python
Data(users).filter(age__gt=30)
Data(users).filter(age__gte=18, age__lt=65)
Data(users).filter(active=True, name__contains="ali")
Data(users).filter(tags__contains="python")
```

Supported lookups:

| Lookup | Meaning |
|---|---|
| `exact` (default) | equality |
| `gt`, `gte` | greater than / greater or equal |
| `lt`, `lte` | less than / less or equal |
| `contains` | substring or membership |
| `startswith`, `endswith` | string prefix/suffix |
| `in` | value in collection |
| `ne` | not equal |

## Selecting fields

```python
Data(users).select("name", "email")
Data(users).select("user.name", "user.email")  # nested
```

## Sorting

```python
Data(users).sort("age")
Data(users).sort("-age")            # descending
Data(users).sort("name", "-age")    # multiple keys
```

## Transforming

```python
Data(users).transform(lambda u: {**u, "name": u["name"].upper()})
Data(users).map(lambda u: u["name"])
```

## Limit, skip, distinct

```python
Data(users).limit(10)
Data(users).skip(5)
Data(users).distinct()
Data(users).distinct("email")
```

## Aggregation

```python
Data(users).count()
Data(users).first()
Data(users).last()
Data(users).pluck("email")
Data(users).group_by("role")
```

## Exporting

```python
Data(users).to("out.json")
Data(users).to("out.csv")
Data(users).to("out.yaml")
Data(users).to("out.xml")
Data(users).to("out.jsonl")
Data(users).to_list()
Data(users).to_dict()
Data(users).to_json()
Data(users).to_csv()
Data(users).to_xml()
Data(users).to_jsonl()
```

## Immutability

Every transformation returns a **new** `Data` instance. The original is never modified.

```python
original = Data([1, 2, 3])
doubled = original.map(lambda x: x * 2)
# original still contains [1, 2, 3]
```