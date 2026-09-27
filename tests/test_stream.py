import csv
import json

import pytest

from datasift import Data, DataError, Stream
from datasift.formats import jsonl_io

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def users_csv(tmp_path):
    p = tmp_path / "users.csv"
    p.write_text(
        "name,age,email\n"
        "Alice,30,alice@example.com\n"
        "Bob,25,bob@example.com\n"
        "Carol,40,carol@example.com\n"
        "Dave,30,dave@example.com\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def users_jsonl(tmp_path):
    p = tmp_path / "users.jsonl"
    lines = [
        json.dumps({"name": "Alice", "age": 30, "email": "alice@example.com"}),
        json.dumps({"name": "Bob", "age": 25, "email": "bob@example.com"}),
        json.dumps({"name": "Carol", "age": 40, "email": "carol@example.com"}),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# JSONL format
# ---------------------------------------------------------------------------

def test_jsonl_roundtrip():
    data = [{"a": 1}, {"b": 2}]
    text = jsonl_io.dumps(data)
    assert jsonl_io.loads(text) == data


def test_jsonl_skips_blank_lines():
    text = '{"a": 1}\n\n{"b": 2}\n'
    assert jsonl_io.loads(text) == [{"a": 1}, {"b": 2}]


# ---------------------------------------------------------------------------
# Stream creation
# ---------------------------------------------------------------------------

def test_from_csv(users_csv):
    stream = Stream.from_csv(str(users_csv))
    assert stream.count() == 4


def test_from_jsonl(users_jsonl):
    stream = Stream.from_jsonl(str(users_jsonl))
    assert stream.count() == 3


def test_from_iterable():
    stream = Stream.from_iterable([1, 2, 3])
    assert stream.to_list() == [1, 2, 3]


def test_from_file_autodetect_csv(users_csv):
    stream = Stream.from_file(str(users_csv))
    assert stream.count() == 4


def test_from_file_autodetect_jsonl(users_jsonl):
    stream = Stream.from_file(str(users_jsonl))
    assert stream.count() == 3


def test_from_file_rejects_json(tmp_path):
    p = tmp_path / "data.json"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(Exception):
        Stream.from_file(str(p))


def test_data_stream_classmethod(users_csv):
    stream = Data.stream(str(users_csv))
    assert stream.count() == 4


# ---------------------------------------------------------------------------
# Lazy transformations
# ---------------------------------------------------------------------------

def test_filter_gt(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .filter(age__gt=30)
        .to_list()
    )
    assert len(result) == 1
    assert result[0]["name"] == "Carol"


def test_filter_bool_style_string(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .filter(name="Alice")
        .to_list()
    )
    assert len(result) == 1


def test_filter_contains(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .filter(name__contains="a")
        .to_list()
    )
    names = {r["name"] for r in result}
    assert "Alice" in names or "Carol" in names or "Dave" in names


def test_select(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .select("name", "age")
        .to_list()
    )
    assert result[0] == {"name": "Alice", "age": "30"}


def test_limit(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .limit(2)
        .to_list()
    )
    assert len(result) == 2


def test_skip(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .skip(2)
        .to_list()
    )
    assert len(result) == 2
    assert result[0]["name"] == "Carol"


def test_map(users_jsonl):
    result = (
        Stream.from_jsonl(str(users_jsonl))
        .map(lambda u: {"n": u["name"]})
        .to_list()
    )
    assert result == [{"n": "Alice"}, {"n": "Bob"}, {"n": "Carol"}]


def test_distinct(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .distinct("age")
        .to_list()
    )
    ages = {r["age"] for r in result}
    assert ages == {"30", "25", "40"}


def test_batch(users_csv):
    batches = (
        Stream.from_csv(str(users_csv))
        .batch(3)
        .to_list()
    )
    assert len(batches) == 2
    assert len(batches[0]) == 3
    assert len(batches[1]) == 1


def test_chained_filter_select(users_csv):
    result = (
        Stream.from_csv(str(users_csv))
        .filter(age__gt=25)
        .select("name")
        .limit(2)
        .to_list()
    )
    assert len(result) == 2
    assert all("name" in r for r in result)


# ---------------------------------------------------------------------------
# Terminal outputs
# ---------------------------------------------------------------------------

def test_to_csv(users_csv, tmp_path):
    out = tmp_path / "filtered.csv"
    (
        Stream.from_csv(str(users_csv))
        .filter(age__gt=25)
        .select("name", "email")
        .to_csv(str(out))
    )
    with open(out, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert rows[0]["name"] == "Alice"


def test_to_jsonl(users_csv, tmp_path):
    out = tmp_path / "out.jsonl"
    (
        Stream.from_csv(str(users_csv))
        .select("name")
        .to_jsonl(str(out))
    )
    with open(out, encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == 4
    assert lines[0] == {"name": "Alice"}


def test_to_data(users_jsonl):
    data = Stream.from_jsonl(str(users_jsonl)).to_data()
    assert isinstance(data, Data)
    assert len(data.data) == 3


def test_first(users_csv):
    result = Stream.from_csv(str(users_csv)).first()
    assert result["name"] == "Alice"


def test_count(users_csv):
    assert Stream.from_csv(str(users_csv)).count() == 4


# ---------------------------------------------------------------------------
# Single-use semantics
# ---------------------------------------------------------------------------

def test_stream_is_single_use(users_csv):
    stream = Stream.from_csv(str(users_csv))
    stream.to_list()
    with pytest.raises(DataError):
        stream.to_list()


def test_cache_allows_reuse(users_csv):
    stream = Stream.from_csv(str(users_csv)).cache()
    assert len(stream.to_list()) == 4


def test_double_terminal_raises(users_csv):
    stream = Stream.from_csv(str(users_csv))
    stream.count()
    with pytest.raises(DataError):
        stream.to_csv("out.csv")
