"""Schema validation using Python's standard typing module.

No external dependencies. Supports:

    - Primitive types: str, int, float, bool, type(None)
    - Containers: list, dict, tuple, set
    - Parameterized generics: List[int], Dict[str, int], Optional[str]
    - Union types: Union[int, str]
    - Literal types: Literal["a", "b"]
    - TypedDict classes
    - Nested schemas (dict of field -> type)

Example:
    from typing import List, Optional
    from typing_extensions import TypedDict
    from datasift import Data
    from datasift.schema import validate, SchemaError

    class User(TypedDict):
        name: str
        age: int
        email: Optional[str]

    data = Data("users.json")
    errors = validate(data.data, List[User])
    if errors:
        for e in errors:
            print(e)
"""

from __future__ import annotations

import typing
from typing import Any, List, Tuple, Union

from .exceptions import DataSiftError


class SchemaError(DataSiftError):
    """Raised when data does not conform to a schema."""

    def __init__(self, path: str, message: str, value: Any = None) -> None:
        self.path = path
        self.message = message
        self.value = value
        super().__init__(f"{path}: {message}")


class ValidationResult:
    """Result of a validation run."""

    def __init__(self, errors: List[SchemaError]) -> None:
        self.errors = errors

    @property
    def ok(self) -> bool:
        return not self.errors

    def __bool__(self) -> bool:
        return self.ok

    def __iter__(self):
        return iter(self.errors)

    def __len__(self) -> int:
        return len(self.errors)

    def __repr__(self) -> str:
        if self.ok:
            return "<ValidationResult ok>"
        return f"<ValidationResult {len(self.errors)} error(s)>"

    def raise_if_invalid(self) -> None:
        """Raise the first error if validation failed."""
        if self.errors:
            raise self.errors[0]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(value: Any, schema: Any) -> ValidationResult:
    """Validate ``value`` against ``schema``.

    Returns a ValidationResult with all errors found. Never raises
    for validation failures (only for invalid schema definitions).
    """
    errors: List[SchemaError] = []
    _validate(value, schema, "$", errors)
    return ValidationResult(errors)


def validate_or_raise(value: Any, schema: Any) -> None:
    """Validate and raise SchemaError on the first failure."""
    result = validate(value, schema)
    result.raise_if_invalid()


def is_valid(value: Any, schema: Any) -> bool:
    """Quick boolean check."""
    return validate(value, schema).ok


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------

def _validate(value: Any, schema: Any, path: str, errors: List[SchemaError]) -> None:
    # --- None / Any -------------------------------------------------------
    if schema is Any:
        return

    if schema is None or schema is type(None):
        if value is not None:
            errors.append(SchemaError(path, f"expected None, got {_type_name(value)}", value))
        return

    # --- TypedDict --------------------------------------------------------
    if _is_typed_dict(schema):
        _validate_typed_dict(value, schema, path, errors)
        return

    # --- Union / Optional ------------------------------------------------
    origin = typing.get_origin(schema)
    args = typing.get_args(schema)

    if origin is Union:
        _validate_union(value, args, path, errors)
        return

    # --- Literal ----------------------------------------------------------
    if origin is typing.Literal or _is_literal(schema):
        _validate_literal(value, args, path, errors)
        return

    # --- Parameterized generics ------------------------------------------
    if origin is list:
        _validate_list(value, args, path, errors)
        return

    if origin is dict:
        _validate_dict(value, args, path, errors)
        return

    if origin is tuple:
        _validate_tuple(value, args, path, errors)
        return

    if origin is set:
        _validate_set(value, args, path, errors)
        return

    # --- Bare containers --------------------------------------------------
    if schema is list:
        if not isinstance(value, list):
            errors.append(SchemaError(path, f"expected list, got {_type_name(value)}", value))
        return

    if schema is dict:
        if not isinstance(value, dict):
            errors.append(SchemaError(path, f"expected dict, got {_type_name(value)}", value))
        return

    if schema is tuple:
        if not isinstance(value, tuple):
            errors.append(SchemaError(path, f"expected tuple, got {_type_name(value)}", value))
        return

    if schema is set:
        if not isinstance(value, set):
            errors.append(SchemaError(path, f"expected set, got {_type_name(value)}", value))
        return

    # --- Dict-based nested schema (fallback) ------------------------------
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            errors.append(SchemaError(path, f"expected dict, got {_type_name(value)}", value))
            return
        for key, sub_schema in schema.items():
            if key not in value:
                errors.append(SchemaError(path, f"missing required key {key!r}", value))
                continue
            _validate(value[key], sub_schema, f"{path}.{key}", errors)
        return

    # --- Primitive types --------------------------------------------------
    if isinstance(schema, type):
        # bool is subclass of int in Python; check bool specifically
        if schema is bool:
            if not isinstance(value, bool):
                errors.append(SchemaError(path, f"expected bool, got {_type_name(value)}", value))
            return
        if schema is int:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(SchemaError(path, f"expected int, got {_type_name(value)}", value))
            return
        if schema is float:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(SchemaError(path, f"expected float, got {_type_name(value)}", value))
            return
        if not isinstance(value, schema):
            errors.append(
                SchemaError(path, f"expected {schema.__name__}, got {_type_name(value)}", value)
            )
        return

    # --- Unknown schema ---------------------------------------------------
    errors.append(SchemaError(path, f"unsupported schema: {schema!r}", value))


# ---------------------------------------------------------------------------
# Validators for specific schema kinds
# ---------------------------------------------------------------------------

def _validate_typed_dict(value: Any, schema: Any, path: str, errors: List[SchemaError]) -> None:
    if not isinstance(value, dict):
        errors.append(SchemaError(path, f"expected dict, got {_type_name(value)}", value))
        return

    hints = typing.get_type_hints(schema)
    required = _required_keys(schema)
    for key, field_type in hints.items():
        if key not in value:
            if key in required:
                errors.append(SchemaError(path, f"missing required key {key!r}", value))
            continue
        _validate(value[key], field_type, f"{path}.{key}", errors)


def _validate_union(value: Any, args: Tuple[Any, ...], path: str, errors: List[SchemaError]) -> None:
    # Try each variant; if any passes, union passes
    for variant in args:
        sub_errors: List[SchemaError] = []
        _validate(value, variant, path, sub_errors)
        if not sub_errors:
            return
    # None matched
    variant_names = " | ".join(_schema_name(a) for a in args)
    errors.append(
        SchemaError(path, f"expected one of ({variant_names}), got {_type_name(value)}", value)
    )


def _validate_literal(value: Any, args: Tuple[Any, ...], path: str, errors: List[SchemaError]) -> None:
    if value not in args:
        allowed = ", ".join(repr(a) for a in args)
        errors.append(SchemaError(path, f"expected one of ({allowed}), got {value!r}", value))


def _validate_list(value: Any, args: Tuple[Any, ...], path: str, errors: List[SchemaError]) -> None:
    if not isinstance(value, list):
        errors.append(SchemaError(path, f"expected list, got {_type_name(value)}", value))
        return
    if not args:
        return
    item_type = args[0]
    for i, item in enumerate(value):
        _validate(item, item_type, f"{path}[{i}]", errors)


def _validate_dict(value: Any, args: Tuple[Any, ...], path: str, errors: List[SchemaError]) -> None:
    if not isinstance(value, dict):
        errors.append(SchemaError(path, f"expected dict, got {_type_name(value)}", value))
        return
    if not args:
        return
    key_type, value_type = args
    for k, v in value.items():
        _validate(k, key_type, f"{path}.<key {k!r}>", errors)
        _validate(v, value_type, f"{path}.{k}", errors)


def _validate_tuple(value: Any, args: Tuple[Any, ...], path: str, errors: List[SchemaError]) -> None:
    if not isinstance(value, tuple):
        errors.append(SchemaError(path, f"expected tuple, got {_type_name(value)}", value))
        return
    if not args:
        return
    # Ellipsis: Tuple[int, ...] means variable length
    if len(args) == 2 and args[1] is Ellipsis:
        item_type = args[0]
        for i, item in enumerate(value):
            _validate(item, item_type, f"{path}[{i}]", errors)
        return
    if len(value) != len(args):
        errors.append(
            SchemaError(path, f"expected tuple of length {len(args)}, got {len(value)}", value)
        )
        return
    for i, (item, item_type) in enumerate(zip(value, args, strict=False)):
        _validate(item, item_type, f"{path}[{i}]", errors)


def _validate_set(value: Any, args: Tuple[Any, ...], path: str, errors: List[SchemaError]) -> None:
    if not isinstance(value, set):
        errors.append(SchemaError(path, f"expected set, got {_type_name(value)}", value))
        return
    if not args:
        return
    item_type = args[0]
    for item in value:
        _validate(item, item_type, f"{path}{{{item!r}}}", errors)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_typed_dict(schema: Any) -> bool:
    return (
        isinstance(schema, type)
        and issubclass(schema, dict)
        and hasattr(schema, "__annotations__")
        and hasattr(schema, "__total__")
    )


def _is_literal(schema: Any) -> bool:
    return typing.get_origin(schema) is typing.Literal


def _required_keys(schema: Any) -> set:
    if getattr(schema, "__total__", True):
        return set(typing.get_type_hints(schema).keys())
    return set()


def _optional_keys(schema: Any) -> set:
    if getattr(schema, "__total__", True):
        return set()
    return set(typing.get_type_hints(schema).keys())


def _type_name(value: Any) -> str:
    if value is None:
        return "None"
    return type(value).__name__


def _schema_name(schema: Any) -> str:
    if schema is type(None):
        return "None"
    if isinstance(schema, type):
        return schema.__name__
    return str(schema)


__all__ = [
    "SchemaError",
    "ValidationResult",
    "is_valid",
    "validate",
    "validate_or_raise",
]
