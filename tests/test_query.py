import pytest

from datasift import QueryError, query

DATA = {
    "users": [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": False},
        {"name": "Carol", "age": 40, "active": True},
    ],
    "config": {"db": {"host": "localhost", "port": 5432}},
    "tags": ["a", "b", "c"],
}


def test_key_path():
    assert query(DATA, "config.db.host") == "localhost"


def test_index():
    assert query(DATA, "users[0].name") == "Alice"


def test_filter_gt():
    assert query(DATA, "users[?age > 30].name") == ["Carol"]


def test_filter_eq_bool():
    assert query(DATA, "users[?active == true].name") == ["Alice", "Carol"]


def test_star():
    assert query(DATA, "tags[*]") == ["a", "b", "c"]


def test_and_or():
    result = query(DATA, "users[?age > 20 && age < 35].name")
    assert result == ["Alice", "Bob"]


def test_invalid_expression():
    with pytest.raises(QueryError):
        query(DATA, "users[?age >]")
