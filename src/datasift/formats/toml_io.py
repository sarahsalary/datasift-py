"""Minimal TOML reader/writer using tomllib (3.11+) with a fallback parser."""

from typing import IO, Any, Dict

try:
    import tomllib as _toml_reader  # Python 3.11+
except ImportError:
    _toml_reader = None


def loads(text: str) -> Dict[str, Any]:
    if _toml_reader is not None:
        return _toml_reader.loads(text)
    return _fallback_loads(text)


def dumps(data: Dict[str, Any]) -> str:
    lines = []
    _write_table(data, [], lines)
    return "\n".join(lines) + "\n"


def read(stream: IO[str]) -> Dict[str, Any]:
    return loads(stream.read())


def write(data: Dict[str, Any], stream: IO[str]) -> None:
    stream.write(dumps(data))


def _fallback_loads(text: str) -> Dict[str, Any]:
    root: Dict[str, Any] = {}
    current = root
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            table = line[1:-1].strip()
            current = root
            for part in table.split("."):
                part = part.strip()
                current = current.setdefault(part, {})
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        current[key] = _parse_scalar(value)
    return root


def _parse_scalar(value: str) -> Any:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(v.strip()) for v in inner.split(",")]
    return value


def _write_table(data: Dict[str, Any], prefix: list, lines: list) -> None:
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}

    if prefix:
        header = ".".join(prefix)
        lines.append(f"[{header}]")

    for key, value in scalars.items():
        lines.append(f"{key} = {_format_scalar(value)}")

    for key, value in tables.items():
        if lines and lines[-1] != "":
            lines.append("")
        _write_table(value, [*prefix, key], lines)


def _format_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        return "[" + ", ".join(_format_scalar(v) for v in value) + "]"
    return f'"{value}"'
