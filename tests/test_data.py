import json

import pytest

from datasift import Data, DataError

USERS = [
    {"name": "Alice", "age": 30, "email": "alice@example.com", "active": True},
    {"name": "Bob", "age": 25, "email": "bob@example.com", "active": False},
    {"name": "Carol", "age": 40, "email": "carol@example.com", "active": True},
    {"name": "Dave", "age": 30, "email": "dave@example.com", "active": True},
]


def test_filter_gt():
    result = Data(USERS).filter(age__gt=30).to_list()
    assert len(result) == 1
    assert result[0]["name"] == "Carol"


def test_filter_gte():
    result = Data(USERS).filter(age__gte=30).to_list()
    assert len(result) == 3


def test_filter_exact():
    result = Data(USERS).filter(name="Alice").to_list()
    assert len(result) == 1


def test_filter_bool():
    result = Data(USERS).filter(active=True).to_list()
    assert len(result) == 3


def test_filter_multiple_conditions():
    result = Data(USERS).filter(active=True, age__gt=30).to_list()
    assert len(result) == 1
    assert result[0]["name"] == "Carol"


def test_filter_contains():
    result = Data(USERS).filter(name__contains="a").to_list()
    names = {u["name"] for u in result}
    assert names == {"Alice", "Carol", "Dave"}


def test_select():
    result = Data(USERS).select("name", "age").to_list()
    assert result[0] == {"name": "Alice", "age": 30}


def test_select_nested():
    data = [{"user": {"name": "Alice", "age": 30}}]
    result = Data(data).select("user.name").to_list()
    assert result[0] == {"user.name": "Alice"}


def test_sort_asc():
    result = Data(USERS).sort("age").to_list()
    ages = [u["age"] for u in result]
    assert ages == [25, 30, 30, 40]


def test_sort_desc():
    result = Data(USERS).sort("-age").to_list()
    ages = [u["age"] for u in result]
    assert ages == [40, 30, 30, 25]


def test_sort_multiple():
    result = Data(USERS).sort("age", "-name").to_list()
    assert result[0]["age"] == 25
    assert result[1]["name"] == "Dave"


def test_chain_filter_select_sort():
    result = (
        Data(USERS)
        .filter(age__gte=30)
        .select("name", "age")
        .sort("-age")
        .to_list()
    )
    assert result[0] == {"name": "Carol", "age": 40}


def test_limit():
    result = Data(USERS).limit(2).to_list()
    assert len(result) == 2


def test_skip():
    result = Data(USERS).skip(2).to_list()
    assert len(result) == 2


def test_distinct():
    data = [{"x": 1}, {"x": 2}, {"x": 1}]
    result = Data(data).distinct().to_list()
    assert len(result) == 2


def test_distinct_field():
    data = [{"x": 1, "y": "a"}, {"x": 1, "y": "b"}, {"x": 2, "y": "c"}]
    result = Data(data).distinct("x").to_list()
    assert len(result) == 2


def test_pluck():
    result = Data(USERS).pluck("name")
    assert result == ["Alice", "Bob", "Carol", "Dave"]


def test_first_last_count():
    d = Data(USERS)
    assert d.first()["name"] == "Alice"
    assert d.last()["name"] == "Dave"
    assert d.count() == 4


def test_transform():
    result = Data([1, 2, 3]).transform(lambda x: x * 2).to_list()
    assert result == [2, 4, 6]


def test_to_json():
    text = Data({"a": 1}).to_json()
    assert json.loads(text) == {"a": 1}


def test_to_file(tmp_path):
    p = tmp_path / "out.json"
    Data(USERS).to(str(p))
    assert json.loads(p.read_text(encoding="utf-8")) == USERS


def test_filter_non_list_raises():
    with pytest.raises(DataError):
        Data({"a": 1}).filter(a=1)


def test_group_by():
    groups = Data(USERS).group_by("active")
    assert len(groups[True]) == 3
    assert len(groups[False]) == 1
