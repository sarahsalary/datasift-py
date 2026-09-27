"""Minimal YAML reader/writer using only the standard library.

This is a deliberately small subset of YAML: mappings, sequences,
scalars, quoted strings, and comments. It is *not* a full YAML
implementation. For full compatibility, install PyYAML separately.
"""

from typing import IO, Any, List


def loads(text: str) -> Any:
    lines = text.splitlines()
    return _parse_block(lines, 0, 0)[0]


def dumps(data: Any, indent: int = 2) -> str:
    lines: List[str] = []
    _dump(data, lines, 0, indent)
    return "\n".join(lines) + "\n"


def read(stream: IO[str]) -> Any:
    return loads(stream.read())


def write(data: Any, stream: IO[str], indent: int = 2) -> None:
    stream.write(dumps(data, indent=indent))


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _count_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: List[str], index: int, base_indent: int):
    while index < len(lines) and (not lines[index].strip() or lines[index].strip().startswith("#")):
        index += 1
    if index >= len(lines):
        return None, index

    first = lines[index]
    indent = _count_indent(first)

    if first.strip().startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(lines: List[str], index: int, indent: int):
    items = []
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        current_indent = _count_indent(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation at line {index + 1}")
        stripped = line.strip()
        if not stripped.startswith("- "):
            break
        rest = stripped[2:].strip()
        if not rest:
            value, index = _parse_block(lines, index + 1, indent + 2)
            items.append(value)
        elif ":" in rest and not rest.startswith('"') and not rest.startswith("'"):
            key, _, val = rest.partition(":")
            item = {key.strip(): _parse_scalar(val.strip()) if val.strip() else None}
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip() or nxt.strip().startswith("#"):
                    index += 1
                    continue
                nxt_indent = _count_indent(nxt)
                if nxt_indent <= indent:
                    break
                if nxt.strip().startswith("- "):
                    break
                k, _, v = nxt.strip().partition(":")
                item[k.strip()] = _parse_scalar(v.strip()) if v.strip() else None
                index += 1
            items.append(item)
        else:
            items.append(_parse_scalar(rest))
            index += 1
    return items, index


def _parse_mapping(lines: List[str], index: int, indent: int):
    result = {}
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        current_indent = _count_indent(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"Unexpected indentation at line {index + 1}")
        stripped = line.strip()
        if stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ValueError(f"Expected 'key: value' at line {index + 1}")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            child, index = _parse_block(lines, index + 1, indent + 1)
            result[key] = child
        else:
            result[key] = _parse_scalar(value)
            index += 1
    return result, index


def _parse_scalar(value: str) -> Any:
    if not value:
        return None
    if value.lower() in ("null", "~"):
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
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


# ---------------------------------------------------------------------------
# Dumper
# ---------------------------------------------------------------------------

def _dump(data: Any, lines: List[str], level: int, indent: int) -> None:
    pad = " " * (level * indent)
    if isinstance(data, dict):
        if not data:
            lines.append(pad + "{}")
            return
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                _dump(value, lines, level + 1, indent)
            else:
                lines.append(f"{pad}{key}: {_format_scalar(value)}")
    elif isinstance(data, list):
        if not data:
            lines.append(pad + "[]")
            return
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(pad + "-")
                _dump(item, lines, level + 1, indent)
            else:
                lines.append(pad + f"- {_format_scalar(item)}")
    else:
        lines.append(pad + _format_scalar(data))


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if any(c in value for c in ":#{}[],&*!|>'\"%@`") or value.strip() != value:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value
    return str(value)
