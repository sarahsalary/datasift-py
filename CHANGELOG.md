# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-09-27

### Fixed
- Fixed fluent `Data` derivations so chained transformations preserve derived data.
- Fixed query tokenization for numeric indexes and closing filter brackets.
- Fixed query projection after list filters, such as `users[?age > 30].name`.
- Fixed CSV numeric comparisons without changing CSV values from strings.
- Fixed case-insensitive string `contains`, `startswith`, and `endswith` lookups.
- Fixed XML list serialization and top-level list handling.
- Added `Data.__len__()` for grouped `Data` results.
- Corrected repository links and release documentation.
## [0.4.0] - 2026-09-27

### Added

- Schema validation with type hints (zero dependencies).
- `Data.validate()` and `Data.expect()` methods.
- `Stream.validate()` and `Stream.expect()` methods.
- `SchemaError`, `ValidationResult`, `validate`, `is_valid`, `validate_or_raise` exports.
- `docs/schema.md` documentation.
- Comprehensive tests for schema validation.

## [0.3.0] - 2026-09-27

### Added

- True streaming for CSV and JSONL via `Stream` class.
- JSONL format support (`jsonl_io.py`).
- `Data.stream()` classmethod.
- `Stream.from_csv`, `Stream.from_jsonl`, `Stream.from_iterable`, `Stream.from_file`.
- Streaming documentation and tests.

## [0.2.0] - 2026-09-27

### Added

- XML format support (`xml_io.py`).
- `Data.to_xml()` method.
- XML documentation and tests.

## [0.1.0] - 2026-09-27

### Added

- Initial release.
- Fluent API (`Data` class).
- Query language (`query.py`).
- Format handlers: JSON, YAML, TOML, CSV.
- CLI (`datasift` command).
- Core API: `load`, `dump`, `convert`, `query_file`.
- Exceptions: `DataSiftError`, `FormatError`, `QueryError`, `DataError`.
- Tests for all core functionality.
- GitHub Actions for release, docs, and CI.
- MkDocs documentation.
