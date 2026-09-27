"""Fluent, chainable API for data manipulation.

This is the core differentiator of datasift-py: a Python-native,
chainable interface for loading, filtering, selecting, sorting,
transforming, and exporting data — without needing to learn jq syntax.

Example:
    from datasift import Data

    result = (
        Data("users.json")
        .filter(age__gt=30)
        .select("name", "email")
        .sort("-age")
        .to("users.csv")
    )

    # Or work with in-memory data:
    data = Data([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
    active = data.filter(age__gte=30).select("name").to_list()
"""

from __future__ import annotations

import os
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)

from .exceptions import DataError, FormatError
from .formats import get_handler
from .schema import ValidationResult


class Data:
    """A fluent, chainable data container.

    Wraps either a file path (loaded lazily) or an in-memory Python
    object (dict, list, etc.). Every transformation method returns a
    new ``Data`` instance, so chains are immutable and reusable.
    """

    def __init__(
        self,
        source: Union[str, os.PathLike, Any],
        fmt: Optional[str] = None,
    ) -> None:
        """Create a Data instance.

        Args:
            source: File path (str/PathLike) or raw Python data (dict, list).
            fmt: Explicit format for file paths. Inferred from extension
                if omitted.
        """
        self._source = source
        self._fmt = fmt
        self._data: Optional[Any] = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Classmethods
    # ------------------------------------------------------------------

    @classmethod
    def stream(cls, path: Union[str, os.PathLike], fmt: Optional[str] = None):
        """Open a stream for large CSV or JSONL files.

        Unlike ``Data(path)``, this does not load the file into memory.
        Returns a ``Stream`` object with the same fluent API.

        Example:
            Data.stream("huge.csv").filter(age__gt=30).to_csv("out.csv")
        """
        from .stream import Stream
        return Stream.from_file(path, fmt=fmt)

    # ------------------------------------------------------------------
    # Loading / access
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> Any:
        if not self._loaded:
            if isinstance(self._source, (str, os.PathLike)):
                path = os.fspath(self._source)
                fmt = self._fmt or _detect_format(path)
                handler = get_handler(fmt)
                try:
                    with open(path, encoding="utf-8") as f:
                        self._data = handler.read(f)
                except OSError as exc:
                    raise FormatError(f"Cannot read {path!r}: {exc}") from exc
            else:
                self._data = self._source
            self._loaded = True
        return self._data

    @property
    def data(self) -> Any:
        """Return the underlying Python object."""
        return self._ensure_loaded()

    # ------------------------------------------------------------------
    # Transformation methods (all return new Data)
    # ------------------------------------------------------------------

    def filter(self, **kwargs: Any) -> Data:
        """Filter a list of dicts by keyword conditions.

        Supports Django-style lookups:
            filter(age__gt=30)
            filter(active=True, name__contains="ali")
            filter(age__gte=18, age__lt=65)
            filter(tags__contains="python")

        Also supports a callable predicate:
            filter(lambda item: item["age"] > 30)
        """
        data = self._ensure_loaded()

        # Support callable predicate
        if len(kwargs) == 1 and "predicate" in kwargs and callable(kwargs["predicate"]):
            predicate = kwargs["predicate"]
            return self._derive([item for item in data if predicate(item)])

        if not isinstance(data, list):
            raise DataError("filter() requires a list at the top level")

        conditions = _build_conditions(kwargs)
        return self._derive([item for item in data if all(c(item) for c in conditions)])

    def select(self, *fields: str) -> Data:
        """Select specific fields from each dict in a list.

        Example:
            select("name", "email")
            select("user.name", "user.email")   # nested paths
        """
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("select() requires a list at the top level")

        def _project(item: Any) -> Any:
            if isinstance(item, dict):
                return {f: _get_path(item, f) for f in fields}
            return item

        return self._derive([_project(item) for item in data])

    def sort(self, *fields: str, reverse: bool = False) -> Data:
        """Sort a list of dicts by one or more fields.

        Prefix a field with ``-`` for descending order:
            sort("age")
            sort("-age")
            sort("name", "-age")
        """
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("sort() requires a list at the top level")

        def _key(item: Any) -> tuple:
            keys = []
            for f in fields:
                descending = f.startswith("-")
                name = f.lstrip("-")
                value = _get_path(item, name) if isinstance(item, dict) else item
                # For mixed types, convert to string for stable comparison
                if isinstance(value, (int, float)):
                    keys.append((0, value))
                else:
                    keys.append((1, str(value)))
                if descending:
                    keys[-1] = _Descending(keys[-1])
            return tuple(keys)

        return self._derive(sorted(data, key=_key, reverse=reverse))

    def transform(self, func: Callable[[Any], Any]) -> Data:
        """Apply a function to the entire dataset (or each item of a list)."""
        data = self._ensure_loaded()
        if isinstance(data, list):
            return self._derive([func(item) for item in data])
        return self._derive(func(data))

    def map(self, func: Callable[[Any], Any]) -> Data:
        """Alias for transform()."""
        return self.transform(func)

    def limit(self, n: int) -> Data:
        """Keep only the first ``n`` items of a list."""
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("limit() requires a list at the top level")
        return self._derive(data[:n])

    def skip(self, n: int) -> Data:
        """Skip the first ``n`` items of a list."""
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("skip() requires a list at the top level")
        return self._derive(data[n:])

    def distinct(self, *fields: str) -> Data:
        """Remove duplicate dicts (optionally by specific fields)."""
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("distinct() requires a list at the top level")

        seen = set()
        result = []
        for item in data:
            if fields:
                key = tuple(_get_path(item, f) for f in fields)
            else:
                key = _freeze(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return self._derive(result)

    def group_by(self, field: str) -> Dict[Any, Data]:
        """Group a list of dicts by a field value.

        Returns a dict mapping group key -> Data instance.
        """
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("group_by() requires a list at the top level")

        groups: Dict[Any, list] = {}
        for item in data:
            key = _get_path(item, field) if isinstance(item, dict) else None
            groups.setdefault(key, []).append(item)
        return {k: self._derive(v) for k, v in groups.items()}

    def pluck(self, field: str) -> List[Any]:
        """Extract a single field from each dict in a list."""
        data = self._ensure_loaded()
        if not isinstance(data, list):
            raise DataError("pluck() requires a list at the top level")
        return [_get_path(item, field) for item in data if isinstance(item, dict)]

    def first(self) -> Any:
        """Return the first item (for lists) or the data itself."""
        data = self._ensure_loaded()
        if isinstance(data, list):
            return data[0] if data else None
        return data

    def last(self) -> Any:
        """Return the last item (for lists) or the data itself."""
        data = self._ensure_loaded()
        if isinstance(data, list):
            return data[-1] if data else None
        return data

    def count(self) -> int:
        """Return the number of items (for lists) or 1."""
        data = self._ensure_loaded()
        if isinstance(data, list):
            return len(data)
        return 1

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def validate(self, schema: Any, raise_on_error: bool = False) -> ValidationResult:
        """Validate the data against a schema.

        Args:
            schema: A type, TypedDict, dict of field->type, or any
                construct supported by ``datasift.schema.validate``.
            raise_on_error: If True, raise SchemaError on first failure
                instead of returning a ValidationResult.

        Returns:
            ValidationResult (always, even if raise_on_error=True and no errors).

        Example:
            from typing import List
            from typing_extensions import TypedDict

            class User(TypedDict):
                name: str
                age: int

            result = Data(users).validate(List[User])
            if not result.ok:
                for err in result:
                    print(err)
        """
        from .schema import validate as _validate

        result = _validate(self._ensure_loaded(), schema)
        if raise_on_error:
            result.raise_if_invalid()
        return result

    def expect(self, schema: Any) -> Data:
        """Validate and raise on failure, returning self for chaining.

        Example:
            Data("users.json").expect(List[User]).filter(age__gt=30).to("out.csv")
        """
        self.validate(schema, raise_on_error=True)
        return self

    # ------------------------------------------------------------------
    # Output methods (terminal)
    # ------------------------------------------------------------------

    def to(self, path: Union[str, os.PathLike], fmt: Optional[str] = None, **kwargs) -> Data:
        """Write to a file. Returns self for further chaining."""
        data = self._ensure_loaded()
        path = os.fspath(path)
        fmt = fmt or _detect_format(path)
        handler = get_handler(fmt)
        text = handler.dumps(data, **kwargs)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return self

    def to_list(self) -> List[Any]:
        """Return the data as a Python list."""
        data = self._ensure_loaded()
        if isinstance(data, list):
            return data
        return [data]

    def to_dict(self) -> Dict[str, Any]:
        """Return the data as a Python dict (if it is one)."""
        data = self._ensure_loaded()
        if isinstance(data, dict):
            return data
        raise DataError(f"Data is {type(data).__name__}, not dict")

    def to_json(self, **kwargs) -> str:
        """Serialize to a JSON string."""
        from .formats import json_io
        return json_io.dumps(self._ensure_loaded(), **kwargs)

    def to_yaml(self, **kwargs) -> str:
        """Serialize to a YAML string."""
        from .formats import yaml_io
        return yaml_io.dumps(self._ensure_loaded(), **kwargs)

    def to_toml(self, **kwargs) -> str:
        """Serialize to a TOML string."""
        from .formats import toml_io
        return toml_io.dumps(self._ensure_loaded(), **kwargs)

    def to_csv(self, **kwargs) -> str:
        """Serialize to a CSV string."""
        from .formats import csv_io
        return csv_io.dumps(self._ensure_loaded(), **kwargs)

    def to_jsonl(self, **kwargs) -> str:
        """Serialize to a JSONL string."""
        from .formats import jsonl_io
        return jsonl_io.dumps(self._ensure_loaded(), **kwargs)

    def to_xml(self, root_tag: Optional[str] = None, **kwargs) -> str:
        """Serialize to an XML string.

        Args:
            root_tag: Explicit root element name. If omitted, the single
                top-level key of a dict is used, or ``<root>`` otherwise.
        """
        from .formats import xml_io
        return xml_io.dumps(self._ensure_loaded(), root_tag=root_tag, **kwargs)

    def __len__(self) -> int:
        """Return the number of top-level records/items.

        For a list this is its length. For any other loaded value, the
        result is ``1`` because the value represents one data object.
        """
        return self.count()

    def __repr__(self) -> str:
        if self._loaded:
            return f"Data({self._data!r})"
        return f"Data(source={self._source!r})"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _derive(self, new_data: Any) -> Data:
        """Create a loaded ``Data`` instance from derived data."""
        obj = Data(new_data)
        obj._data = new_data
        obj._loaded = True
        return obj


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if not ext:
        raise FormatError(f"Cannot detect format from path: {path!r}")
    return ext


def _get_path(obj: Any, path: str) -> Any:
    """Get a nested value using dot notation."""
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _freeze(obj: Any) -> Any:
    """Convert a nested structure to a hashable representation."""
    if isinstance(obj, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in obj.items()))
    if isinstance(obj, (list, tuple)):
        return tuple(_freeze(v) for v in obj)
    return obj


class _Descending:
    """Wrapper that reverses comparison order for descending sorts."""
    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        self.value = value

    def __lt__(self, other: _Descending) -> bool:
        return self.value > other.value

    def __gt__(self, other: _Descending) -> bool:
        return self.value < other.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _Descending):
            return self.value == other.value
        return NotImplemented


def _safe_compare(actual: Any, expected: Any, operator: str) -> bool:
    """Compare values while allowing numeric strings from CSV to be queried.

    CSV readers intentionally preserve source values as strings. When a
    lookup compares a numeric string such as ``"30"`` with an ``int`` such
    as ``30``, the values are normalized only for the comparison; the
    original record remains unchanged.
    """
    if actual is None:
        return operator == "==" and expected is None

    left, right = actual, expected

    if isinstance(left, str) and isinstance(right, (int, float)) and not isinstance(right, bool):
        try:
            left = float(left) if isinstance(right, float) else int(left)
        except ValueError:
            return False
    elif isinstance(right, str) and isinstance(left, (int, float)) and not isinstance(left, bool):
        try:
            right = float(right) if isinstance(left, float) else int(right)
        except ValueError:
            return False

    try:
        if operator == "==":
            return left == right
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
    except TypeError:
        return False

    raise DataError(f"Unsupported comparison operator: {operator!r}")


def _build_conditions(kwargs: Dict[str, Any]) -> List[Callable[[Any], bool]]:
    """Build predicate functions from Django-style kwargs."""
    conditions: List[Callable[[Any], bool]] = []

    for key, value in kwargs.items():
        # Parse lookup suffix
        if "__" in key:
            field, _, lookup = key.rpartition("__")
        else:
            field, lookup = key, "exact"

        def make_predicate(f: str, lk: str, v: Any) -> Callable[[Any], bool]:
            def predicate(item: Any) -> bool:
                actual = _get_path(item, f) if isinstance(item, dict) else None
                if lk == "exact":
                    return _safe_compare(actual, v, "==")
                if lk == "gt":
                    return _safe_compare(actual, v, ">")
                if lk == "gte":
                    return _safe_compare(actual, v, ">=")
                if lk == "lt":
                    return _safe_compare(actual, v, "<")
                if lk == "lte":
                    return _safe_compare(actual, v, "<=")
                if lk == "contains":
                    if isinstance(actual, str):
                        return str(v).lower() in actual.lower()
                    if isinstance(actual, (list, tuple)):
                        return v in actual
                    return False
                if lk == "startswith":
                    return (
                        isinstance(actual, str)
                        and actual.lower().startswith(str(v).lower())
                    )
                if lk == "endswith":
                    return (
                        isinstance(actual, str)
                        and actual.lower().endswith(str(v).lower())
                    )
                if lk == "in":
                    return actual in v
                if lk == "ne":
                    return actual != v
                raise DataError(f"Unsupported lookup: {lk!r}")
            return predicate

        conditions.append(make_predicate(field, lookup, value))

    return conditions


__all__ = ["Data"]
