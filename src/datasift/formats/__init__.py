"""Format handlers registry."""

from . import csv_io, json_io, jsonl_io, toml_io, xml_io, yaml_io

HANDLERS = {
    "json": json_io,
    "jsonl": jsonl_io,
    "ndjson": jsonl_io,
    "yaml": yaml_io,
    "yml": yaml_io,
    "toml": toml_io,
    "csv": csv_io,
    "xml": xml_io,
}

ALIASES = {
    "yml": "yaml",
    "ndjson": "jsonl",
}

STREAMABLE_FORMATS = {"csv", "jsonl"}


def get_handler(name: str):
    key = name.lower().lstrip(".")
    key = ALIASES.get(key, key)
    if key not in HANDLERS:
        raise ValueError(f"Unsupported format: {name!r}")
    return HANDLERS[key]


def supported_formats():
    return sorted(set(HANDLERS) - set(ALIASES))


def is_streamable(fmt: str) -> bool:
    key = fmt.lower().lstrip(".")
    key = ALIASES.get(key, key)
    return key in STREAMABLE_FORMATS
