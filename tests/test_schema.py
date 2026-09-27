import sys
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union

import pytest

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from datasift import Data, SchemaError, Stream, is_valid, validate, validate_or_raise

# ---------------------------------------------------------------------------
# Fixtures / schemas
# ---------------------------------------------------------------------------

class User(TypedDict):
    name: str
    age: int
    email: str


class OptionalUser(TypedDict, total=False):
    name: str
    age: int


USERS_VALID = [
    {"name": "Alice", "age": 30, "email": "alice@example.com"},
    {"name": "Bob", "age": 25, "email": "bob@example.com"},
]

USERS_INVALID_AGE = [
    {"name": "Alice", "age": "30", "email": "alice@example.com"},
]

USERS_MISSING_FIELD = [
    {"name": "Alice", "age": 30},
]


# ---------------------------------------------------------------------------
# Primitive types
# ---------------------------------------------------------------------------

def test_validate_str_ok():
    assert validate("hello", str).ok


def test_validate_str_fail():
    result = validate(42, str)
    assert not result.ok
    assert "expected str" in result.errors[0].message


def test_validate_int_ok():
    assert validate(42, int).ok


def test_validate_int_rejects_bool():
    assert not validate(True, int).ok


def test_validate_float_accepts_int():
    assert validate(42, float).ok


def test_validate_bool_ok():
    assert validate(True, bool).ok
    assert validate(False, bool).ok


def test_validate_none():
    assert validate(None, type(None)).ok
    assert not validate(0, type(None)).ok


def test_validate_any():
    assert validate("anything", Any).ok
    assert validate({"nested": [1, 2]}, Any).ok


# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

def test_validate_list_of_int():
    assert validate([1, 2, 3], List[int]).ok


def test_validate_list_of_int_fail():
    result = validate([1, "2", 3], List[int])
    assert not result.ok
    assert "$[1]" in str(result.errors[0])


def test_validate_dict_str_int():
    assert validate({"a": 1, "b": 2}, Dict[str, int]).ok


def test_validate_dict_fail_value():
    result = validate({"a": "x"}, Dict[str, int])
    assert not result.ok


def test_validate_tuple_fixed():
    assert validate((1, "a"), Tuple[int, str]).ok


def test_validate_tuple_wrong_length():
    result = validate((1,), Tuple[int, str])
    assert not result.ok
    assert "length 2" in result.errors[0].message


def test_validate_tuple_variable():
    assert validate((1, 2, 3), Tuple[int, ...]).ok


def test_validate_set():
    assert validate({1, 2, 3}, Set[int]).ok


# ---------------------------------------------------------------------------
# Union / Optional
# ---------------------------------------------------------------------------

def test_validate_union_ok():
    assert validate(42, Union[int, str]).ok
    assert validate("hi", Union[int, str]).ok


def test_validate_union_fail():
    result = validate(3.14, Union[int, str])
    assert not result.ok


def test_validate_optional():
    assert validate(None, Optional[str]).ok
    assert validate("hi", Optional[str]).ok
    assert not validate(42, Optional[str]).ok


# ---------------------------------------------------------------------------
# Literal
# ---------------------------------------------------------------------------

def test_validate_literal_ok():
    assert validate("a", Literal["a", "b"]).ok


def test_validate_literal_fail():
    result = validate("c", Literal["a", "b"])
    assert not result.ok


# ---------------------------------------------------------------------------
# TypedDict
# ---------------------------------------------------------------------------

def test_validate_typeddict_ok():
    assert validate({"name": "Alice", "age": 30, "email": "a@b.com"}, User).ok


def test_validate_typeddict_missing_field():
    result = validate({"name": "Alice", "age": 30}, User)
    assert not result.ok
    assert any("email" in e.message for e in result.errors)


def test_validate_typeddict_wrong_type():
    result = validate({"name": "Alice", "age": "30", "email": "a@b.com"}, User)
    assert not result.ok
    assert any("$.age" in str(e) for e in result.errors)


def test_validate_typeddict_total_false():
    assert validate({}, OptionalUser).ok
    assert validate({"name": "Alice"}, OptionalUser).ok


def test_validate_typeddict_not_dict():
    result = validate([1, 2], User)
    assert not result.ok
    assert "expected dict" in result.errors[0].message


# ---------------------------------------------------------------------------
# Nested schemas
# ---------------------------------------------------------------------------

def test_validate_list_of_typeddict():
    assert validate(USERS_VALID, List[User]).ok


def test_validate_list_of_typeddict_fail():
    result = validate(USERS_INVALID_AGE, List[User])
    assert not result.ok
    assert "$[0].age" in str(result.errors[0])


def test_validate_nested_typeddict():
    class Address(TypedDict):
        city: str
        zip: str

    class Person(TypedDict):
        name: str
        address: Address

    good = {"name": "A", "address": {"city": "X", "zip": "12345"}}
    bad = {"name": "A", "address": {"city": "X"}}
    assert validate(good, Person).ok
    assert not validate(bad, Person).ok


def test_validate_dict_schema_fallback():
    schema = {"name": str, "age": int}
    assert validate({"name": "A", "age": 1}, schema).ok
    assert not validate({"name": "A"}, schema).ok


# ---------------------------------------------------------------------------
# validate_or_raise
# ---------------------------------------------------------------------------

def test_validate_or_raise_ok():
    validate_or_raise("hi", str)


def test_validate_or_raise_raises():
    with pytest.raises(SchemaError) as exc_info:
        validate_or_raise(42, str)
    assert "expected str" in str(exc_info.value)


# ---------------------------------------------------------------------------
# is_valid
# ---------------------------------------------------------------------------

def test_is_valid_true():
    assert is_valid("hi", str)


def test_is_valid_false():
    assert not is_valid(42, str)


# ---------------------------------------------------------------------------
# Data integration
# ---------------------------------------------------------------------------

def test_data_validate_ok():
    result = Data(USERS_VALID).validate(List[User])
    assert result.ok


def test_data_validate_fail():
    result = Data(USERS_INVALID_AGE).validate(List[User])
    assert not result.ok


def test_data_expect_chains():
    # expect() returns self for chaining
    d = Data(USERS_VALID).expect(List[User])
    assert isinstance(d, Data)


def test_data_expect_raises():
    with pytest.raises(SchemaError):
        Data(USERS_INVALID_AGE).expect(List[User])


def test_data_expect_then_filter():
    result = (
        Data(USERS_VALID)
        .expect(List[User])
        .filter(age__gt=28)
        .to_list()
    )
    assert len(result) == 1
    assert result[0]["name"] == "Alice"


def test_data_validate_raise_on_error():
    with pytest.raises(SchemaError):
        Data(USERS_INVALID_AGE).validate(List[User], raise_on_error=True)


# ---------------------------------------------------------------------------
# Stream integration
# ---------------------------------------------------------------------------

def test_stream_validate_ok(tmp_path):
    import json
    p = tmp_path / "users.jsonl"
    p.write_text("\n".join(json.dumps(u) for u in USERS_VALID) + "\n", encoding="utf-8")
    result = Stream.from_jsonl(str(p)).validate(User, sample=10)
    assert result.ok


def test_stream_validate_fail(tmp_path):
    import json
    p = tmp_path / "users.jsonl"
    p.write_text("\n".join(json.dumps(u) for u in USERS_INVALID_AGE) + "\n", encoding="utf-8")
    result = Stream.from_jsonl(str(p)).validate(User, sample=10)
    assert not result.ok


def test_stream_expect_raises(tmp_path):
    import json
    p = tmp_path / "users.jsonl"
    p.write_text(json.dumps(USERS_INVALID_AGE[0]) + "\n", encoding="utf-8")
    with pytest.raises(SchemaError):
        Stream.from_jsonl(str(p)).expect(User, sample=1)
