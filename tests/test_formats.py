

from datasift import Data


def test_json_roundtrip(tmp_path):
    p = tmp_path / "data.json"
    data = {"a": 1, "b": [2, 3]}
    Data(data).to(str(p))
    loaded = Data(str(p)).data
    assert loaded == data


def test_yaml_roundtrip(tmp_path):
    p = tmp_path / "data.yaml"
    data = {"name": "Alice", "age": 30, "tags": ["a", "b"]}
    Data(data).to(str(p))
    loaded = Data(str(p)).data
    assert loaded["name"] == "Alice"
    assert loaded["age"] == 30


def test_toml_roundtrip(tmp_path):
    p = tmp_path / "data.toml"
    data = {"title": "Test", "count": 5, "nested": {"x": 1}}
    Data(data).to(str(p))
    loaded = Data(str(p)).data
    assert loaded["title"] == "Test"
    assert loaded["nested"]["x"] == 1


def test_csv_roundtrip(tmp_path):
    p = tmp_path / "data.csv"
    rows = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    Data(rows).to(str(p))
    loaded = Data(str(p)).data
    assert len(loaded) == 2
    assert loaded[0]["name"] == "Alice"


def test_jsonl_roundtrip(tmp_path):
    p = tmp_path / "data.jsonl"
    rows = [{"a": 1}, {"b": 2}]
    Data(rows).to(str(p))
    loaded = Data(str(p)).data
    assert loaded == rows
