"""datasift — zero-dependency data format converter, query engine, and validator.

Public API:
    from datasift import Data, Stream, load, dump, convert, query_file
    from datasift import query as query_data
    from datasift.schema import validate, SchemaError, ValidationResult

    # Fluent API (in-memory)
    Data("users.json").filter(age__gt=30).select("name").to("names.csv")

    # Streaming API (large files, low memory)
    Stream.from_csv("huge.csv").filter(age__gt=30).to_csv("filtered.csv")

    # Schema validation
    from typing import List
    from typing_extensions import TypedDict

    class User(TypedDict):
        name: str
        age: int

    Data("users.json").expect(List[User]).to("validated.csv")
"""

from .core import convert, detect_format, dump, load, query_file, supported_formats
from .data import Data
from .exceptions import DataError, DataSiftError, FormatError, QueryError
from .query import compile_query, query
from .schema import (
    SchemaError,
    ValidationResult,
    is_valid,
    validate,
    validate_or_raise,
)
from .stream import Stream

__version__ = "0.4.1"

__all__ = [
    "Data",
    "DataError",
    "DataSiftError",
    "FormatError",
    "QueryError",
    "SchemaError",
    "Stream",
    "ValidationResult",
    "__version__",
    "compile_query",
    "convert",
    "detect_format",
    "dump",
    "is_valid",
    "load",
    "query",
    "query_file",
    "supported_formats",
    "validate",
    "validate_or_raise",
]
