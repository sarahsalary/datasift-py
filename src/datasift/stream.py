"""Lazy, single-pass streaming API for large datasets.

Unlike ``Data``, which loads everything into memory, ``Stream`` works
on iterators and processes records one at a time. It is designed for
CSV and JSONL files that don't fit in memory.

Example:
    from datasift import Stream

    (
        Stream.from_csv("huge.csv")
        .filter(age__gt=30)
        .select("name", "email")
        .to_csv("filtered.csv")
    )

Important:
    Streams are single-use. Once consumed (by ``to_csv``, ``to_list``,
    ``for_each``, or iteration), the underlying iterator is exhausted.
    If you need to reuse the data, call ``.cache()`` first to materialize
    it, or re-create the Stream.
"""

from __future__ import annotations

import csv
import os
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Union,
)

from .exceptions import DataError, FormatError
from .formats import jsonl_io
from .schema import ValidationResult


class Stream:
    """A lazy, chainable stream of records.

    Every transformation method returns a new ``Stream`` wrapping a
    generator that pulls from the previous one. Nothing is evaluated
    until a terminal method (``to_csv``, ``to_jsonl``, ``to_list``,
    ``for_each``) is called.
    """

    def __init__(self, iterator: Iterator[Any], source: Optional[str] = None) -> None:
        self._iterator = iterator
        self._source = source
        self._consumed = False

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_csv(cls, path: Union[str, os.PathLike], **kwargs: Any) -> Stream:
        """Open a CSV file as a stream of dicts.

        Args:
            path: File path, or ``"-"`` for stdin.
            **kwargs: Passed to ``csv.DictReader`` (delimiter, quotechar, ...).
        """
        path_str = os.fspath(path)

        def gen() -> Iterator[Dict[str, Any]]:
            if path_str == "-":
                reader = csv.DictReader(sys.stdin, **kwargs)
                for row in reader:
                    yield dict(row)
            else:
                with open(path_str, encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f, **kwargs)
                    for row in reader:
                        yield dict(row)

        return cls(gen(), source=path_str)

    @classmethod
    def from_jsonl(cls, path: Union[str, os.PathLike]) -> Stream:
        """Open a JSONL file as a stream of parsed values."""
        path_str = os.fspath(path)

        def gen() -> Iterator[Any]:
            if path_str == "-":
                yield from jsonl_io.iter_read(sys.stdin)
            else:
                with open(path_str, encoding="utf-8") as f:
                    yield from jsonl_io.iter_read(f)

        return cls(gen(), source=path_str)

    @classmethod
    def from_iterable(cls, iterable: Iterable[Any]) -> Stream:
        """Create a Stream from any Python iterable."""
        return cls(iter(iterable))

    @classmethod
    def from_file(cls, path: Union[str, os.PathLike], fmt: Optional[str] = None) -> Stream:
        """Auto-detect format and open a stream.

        Only CSV and JSONL are streamable. For other formats, use
        ``Data`` instead.
        """
        path_str = os.fspath(path)
        fmt = (fmt or os.path.splitext(path_str)[1].lstrip(".")).lower()
        if fmt == "csv":
            return cls.from_csv(path_str)
        if fmt in ("jsonl", "ndjson"):
            return cls.from_jsonl(path_str)
        raise FormatError(
            f"Streaming is not supported for format {fmt!r}. "
            f"Use Data({path_str!r}) for in-memory loading."
        )

    # ------------------------------------------------------------------
    # Lazy transformations
    # ------------------------------------------------------------------

    def filter(self, **kwargs: Any) -> Stream:
        """Filter records by Django-style conditions (lazy)."""
        from .data import _build_conditions

        if len(kwargs) == 1 and "predicate" in kwargs and callable(kwargs["predicate"]):
            predicate = kwargs["predicate"]

            def gen_pred() -> Iterator[Any]:
                for item in self._iterator:
                    if predicate(item):
                        yield item

            return Stream(gen_pred())

        conditions = _build_conditions(kwargs)

        def gen() -> Iterator[Any]:
            for item in self._iterator:
                if all(c(item) for c in conditions):
                    yield item

        return Stream(gen())

    def select(self, *fields: str) -> Stream:
        """Keep only the given fields in each record (lazy)."""
        from .data import _get_path

        def gen() -> Iterator[Any]:
            for item in self._iterator:
                if isinstance(item, dict):
                    yield {f: _get_path(item, f) for f in fields}
                else:
                    yield item

        return Stream(gen())

    def map(self, func: Callable[[Any], Any]) -> Stream:
        """Apply a function to each record (lazy)."""

        def gen() -> Iterator[Any]:
            for item in self._iterator:
                yield func(item)

        return Stream(gen())

    def transform(self, func: Callable[[Any], Any]) -> Stream:
        """Alias for map()."""
        return self.map(func)

    def limit(self, n: int) -> Stream:
        """Stop after ``n`` records."""

        def gen() -> Iterator[Any]:
            count = 0
            for item in self._iterator:
                if count >= n:
                    return
                yield item
                count += 1

        return Stream(gen())

    def skip(self, n: int) -> Stream:
        """Skip the first ``n`` records."""

        def gen() -> Iterator[Any]:
            iterator = iter(self._iterator)
            for _ in range(n):
                try:
                    next(iterator)
                except StopIteration:
                    return
            yield from iterator

        return Stream(gen())

    def distinct(self, *fields: str) -> Stream:
        """Yield unique records (lazy, but keeps a seen-set in memory)."""
        from .data import _freeze, _get_path

        def gen() -> Iterator[Any]:
            seen = set()
            for item in self._iterator:
                if fields:
                    key = tuple(_get_path(item, f) for f in fields)
                else:
                    key = _freeze(item)
                if key not in seen:
                    seen.add(key)
                    yield item

        return Stream(gen())

    def batch(self, size: int) -> Stream:
        """Group records into lists of ``size`` items.

        Useful for bulk database inserts.
        """
        if size <= 0:
            raise DataError("batch size must be positive")

        def gen() -> Iterator[List[Any]]:
            batch: List[Any] = []
            for item in self._iterator:
                batch.append(item)
                if len(batch) >= size:
                    yield batch
                    batch = []
            if batch:
                yield batch

        return Stream(gen())

    def for_each(self, func: Callable[[Any], None]) -> None:
        """Apply a side-effecting function to each record (terminal)."""
        self._ensure_not_consumed()
        for item in self._iterator:
            func(item)
        self._consumed = True

    def cache(self) -> Stream:
        """Materialize the stream into a list and return a re-iterable Stream.

        Use this only when the data fits in memory. The original stream
        is consumed; the returned stream can be iterated multiple times.
        """
        self._ensure_not_consumed()
        items = list(self._iterator)
        self._consumed = True
        return Stream(iter(items))

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def validate(self, schema: Any, sample: int = 1000) -> ValidationResult:
        """Validate up to ``sample`` records against a schema.

        Note: streaming validation is inherently limited because it can
        only see the records it has pulled. Set ``sample`` high enough
        to cover a representative portion, or use ``.cache()`` for full
        validation on small datasets.

        Args:
            schema: Any schema supported by ``datasift.schema.validate``.
            sample: Maximum number of records to check.

        Returns:
            ValidationResult with all errors found in the sampled records.
        """
        from .schema import SchemaError
        from .schema import validate as _validate

        self._ensure_not_consumed()
        errors: List[SchemaError] = []
        checked = 0
        for item in self._iterator:
            result = _validate(item, schema)
            errors.extend(result.errors)
            checked += 1
            if checked >= sample:
                break
        self._consumed = True

        from .schema import ValidationResult
        return ValidationResult(errors)

    def expect(self, schema: Any, sample: int = 1000) -> Stream:
        """Validate up to ``sample`` records and raise on first failure.

        Returns self for chaining. Note: because the stream is consumed
        by validation, this method cannot be chained with further
        transformations. Use ``validate()`` instead if you need to
        continue processing.
        """
        result = self.validate(schema, sample=sample)
        result.raise_if_invalid()
        return self

    # ------------------------------------------------------------------
    # Terminal outputs
    # ------------------------------------------------------------------

    def to_csv(
        self,
        path: Union[str, os.PathLike],
        fieldnames: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Write records to a CSV file, one row at a time."""
        self._ensure_not_consumed()
        path_str = os.fspath(path)

        if path_str == "-":
            out = sys.stdout
            close = False
        else:
            out = open(path_str, "w", encoding="utf-8", newline="")
            close = True

        try:
            writer: Optional[csv.DictWriter] = None
            for item in self._iterator:
                if writer is None:
                    if fieldnames is None:
                        if not isinstance(item, dict):
                            raise DataError(
                                "CSV output requires dict records "
                                "(or explicit fieldnames)"
                            )
                        fieldnames = list(item.keys())
                    writer = csv.DictWriter(
                        out, fieldnames=fieldnames,
                        extrasaction="ignore", **kwargs,
                    )
                    writer.writeheader()
                if not isinstance(item, dict):
                    raise DataError("CSV output requires dict records")
                writer.writerow({k: ("" if v is None else v) for k, v in item.items()})
        finally:
            if close:
                out.close()

        self._consumed = True

    def to_jsonl(self, path: Union[str, os.PathLike], **kwargs: Any) -> None:
        """Write records to a JSONL file, one line at a time."""
        self._ensure_not_consumed()
        path_str = os.fspath(path)

        if path_str == "-":
            out = sys.stdout
            close = False
        else:
            out = open(path_str, "w", encoding="utf-8")
            close = True

        try:
            jsonl_io.iter_write(iter(self._iterator), out, **kwargs)
        finally:
            if close:
                out.close()

        self._consumed = True

    def to_list(self) -> List[Any]:
        """Materialize the stream into a list (terminal)."""
        self._ensure_not_consumed()
        result = list(self._iterator)
        self._consumed = True
        return result

    def to_data(self):
        """Materialize into a ``Data`` instance (terminal)."""
        from .data import Data

        items = self.to_list()
        return Data(items)

    def count(self) -> int:
        """Count records, consuming the stream (terminal)."""
        self._ensure_not_consumed()
        total = 0
        for _ in self._iterator:
            total += 1
        self._consumed = True
        return total

    def first(self) -> Any:
        """Return the first record (terminal, consumes at most one item)."""
        self._ensure_not_consumed()
        try:
            result = next(iter(self._iterator))
        except StopIteration:
            result = None
        self._consumed = True
        return result

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[Any]:
        self._ensure_not_consumed()
        self._consumed = True
        return self._iterator

    def _ensure_not_consumed(self) -> None:
        if self._consumed:
            raise DataError(
                "This Stream has already been consumed. "
                "Streams are single-use. Use .cache() or re-create the Stream."
            )

    def __repr__(self) -> str:
        status = "consumed" if self._consumed else "open"
        src = f" source={self._source!r}" if self._source else ""
        return f"<Stream {status}{src}>"


__all__ = ["Stream"]
