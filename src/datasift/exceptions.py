"""Exceptions used across datasift."""


class DataSiftError(Exception):
    """Base exception for datasift."""


class FormatError(DataSiftError):
    """Raised when reading or writing a data format fails."""


class QueryError(DataSiftError):
    """Raised when a query expression is invalid or fails at runtime."""


class DataError(DataSiftError):
    """Raised when data manipulation fails (filter, select, sort, etc.)."""
