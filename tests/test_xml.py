import pytest

from datasift import Data
from datasift.formats import xml_io

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def test_xml_simple_text():
    xml = "<name>Alice</name>"
    assert xml_io.loads(xml) == {"name": "Alice"}


def test_xml_type_inference():
    xml = "<root><a>42</a><b>3.14</b><c>true</c><d>false</d><e>null</e></root>"
    result = xml_io.loads(xml)
    assert result["root"] == {"a": 42, "b": 3.14, "c": True, "d": False, "e": None}


def test_xml_attributes():
    xml = '<user id="1" active="true"><name>Alice</name></user>'
    result = xml_io.loads(xml)
    assert result["user"]["@id"] == 1
    assert result["user"]["@active"] is True
    assert result["user"]["name"] == "Alice"


def test_xml_repeated_children_become_list():
    xml = "<items><item>a</item><item>b</item><item>c</item></items>"
    result = xml_io.loads(xml)
    assert result["items"]["item"] == ["a", "b", "c"]


def test_xml_nested():
    xml = """
    <users>
      <user id="1"><name>Alice</name><age>30</age></user>
      <user id="2"><name>Bob</name><age>25</age></user>
    </users>
    """
    result = xml_io.loads(xml)
    users = result["users"]["user"]
    assert len(users) == 2
    assert users[0]["@id"] == 1
    assert users[0]["name"] == "Alice"
    assert users[1]["age"] == 25


def test_xml_text_with_attributes():
    xml = '<item id="1">hello</item>'
    result = xml_io.loads(xml)
    assert result["item"]["@id"] == 1
    assert result["item"]["#text"] == "hello"


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_xml_dumps_simple():
    text = xml_io.dumps({"name": "Alice"}, xml_declaration=False)
    assert "<name>Alice</name>" in text


def test_xml_dumps_attributes():
    text = xml_io.dumps({"user": {"@id": 1, "name": "Alice"}}, xml_declaration=False)
    assert 'id="1"' in text
    assert "<name>Alice</name>" in text


def test_xml_dumps_with_declaration():
    text = xml_io.dumps({"name": "Alice"})
    assert text.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_xml_dumps_multiple_top_level_keys():
    text = xml_io.dumps({"a": 1, "b": 2}, xml_declaration=False)
    assert "<root>" in text
    assert "<a>1</a>" in text
    assert "<b>2</b>" in text


def test_xml_dumps_top_level_list_with_root_tag():
    data = [{"name": "Alice"}, {"name": "Bob"}]
    text = xml_io.dumps(data, root_tag="users", xml_declaration=False)
    assert "<users>" in text
    assert text.count("<user>") == 2


def test_xml_dumps_top_level_list_requires_root_tag():
    with pytest.raises(ValueError, match="root_tag"):
        xml_io.dumps([{"name": "Alice"}])


# ---------------------------------------------------------------------------
# Round-trips
# ---------------------------------------------------------------------------

def test_xml_roundtrip_simple():
    data = {"name": "Alice", "age": 30}
    text = xml_io.dumps(data)
    assert xml_io.loads(text) == {"root": data}


def test_xml_roundtrip_attributes():
    data = {"user": {"@id": 1, "name": "Alice", "age": 30}}
    text = xml_io.dumps(data)
    assert xml_io.loads(text) == data


def test_xml_roundtrip_list():
    data = {"items": {"item": ["a", "b", "c"]}}
    text = xml_io.dumps(data)
    assert xml_io.loads(text) == data


def test_xml_roundtrip_nested_users():
    data = {
        "users": {
            "user": [
                {"@id": 1, "name": "Alice", "age": 30},
                {"@id": 2, "name": "Bob", "age": 25},
            ]
        }
    }
    text = xml_io.dumps(data)
    assert xml_io.loads(text) == data


def test_xml_roundtrip_with_text_and_attrs():
    data = {"item": {"@id": 1, "#text": "hello"}}
    text = xml_io.dumps(data)
    assert xml_io.loads(text) == data


# ---------------------------------------------------------------------------
# Fluent API integration
# ---------------------------------------------------------------------------

def test_fluent_to_xml():
    users = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    text = Data(users).to_xml(root_tag="users")
    assert "<users>" in text
    assert "<name>Alice</name>" in text


def test_fluent_filter_then_xml():
    users = [
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
        {"name": "Carol", "age": 40},
    ]
    text = (
        Data(users)
        .filter(age__gt=28)
        .select("name")
        .to_xml(root_tag="adults")
    )
    assert "Alice" in text
    assert "Carol" in text
    assert "Bob" not in text


def test_fluent_from_xml(tmp_path):
    p = tmp_path / "users.xml"
    p.write_text(
        '<users><user><name>Alice</name><age>30</age></user></users>',
        encoding="utf-8",
    )
    data = Data(str(p))
    assert data.data["users"]["user"]["name"] == "Alice"
