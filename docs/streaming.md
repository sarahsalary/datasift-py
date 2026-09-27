# Streaming

For CSV and JSONL files that don't fit in memory, use the `Stream` API.
It processes records one at a time and never loads the whole file.

## Reading

```python
from datasift import Stream, Data

# CSV
stream = Stream.from_csv("huge.csv")

# JSONL
stream = Stream.from_jsonl("events.jsonl")

# Auto-detect from extension
stream = Stream.from_file("huge.csv")
stream = Stream.from_file("events.jsonl")

# From any iterable
stream = Stream.from_iterable([1, 2, 3])

# From Data
stream = Data.stream("huge.csv")
```

## Transforming

```python
(
    Stream.from_csv("huge.csv")
    .filter(age__gt=30)
    .select("name", "email")
    .map(lambda r: {**r, "name": r["name"].upper()})
    .limit(1000)
)
```

## Writing

```python
(
    Stream.from_csv("huge.csv")
    .filter(age__gt=30)
    .to_csv("filtered.csv")
)

(
    Stream.from_jsonl("events.jsonl")
    .filter(event_type="purchase")
    .to_jsonl("purchases.jsonl")
)
```

## Batching

Useful for bulk database inserts:

```python
for batch in Stream.from_csv("data.csv").batch(1000):
    db.insert_many(batch)
```

## Counting without loading

```python
total = Stream.from_csv("huge.csv").count()
```

## Getting the first record

```python
first = Stream.from_csv("huge.csv").first()
```

## Converting to Data

If the stream is small enough, materialize it:

```python
data = Stream.from_csv("small.csv").to_data()
data.filter(age__gt=30).to("out.csv")
```

## Important

- Streams are **single-use**. Once consumed, they cannot be iterated again.
- Use `.cache()` if you need to reuse the data:

```python
stream = Stream.from_csv("data.csv").cache()
len(stream.to_list())  # works
len(stream.to_list())  # works again
```

- Only **CSV** and **JSONL** support true streaming.
- `distinct()` keeps a seen-set in memory but does not hold the whole dataset.
- Use `"-"` as the path to read from stdin or write to stdout:

```python
Stream.from_csv("-")        # read from stdin
Stream.from_csv("data.csv").to_csv("-")  # write to stdout
```