"""XML reader/writer using only the standard library.

Python representation:

    XML:
        <users>
          <user id="1"><name>Alice</name><age>30</age></user>
          <user id="2"><name>Bob</name><age>25</age></user>
        </users>

    Python:
        {
          "users": {
            "user": [
              {"@id": 1, "name": "Alice", "age": 30},
              {"@id": 2, "name": "Bob", "age": 25}
            ]
          }
        }

Rules:
    - The root element becomes a single-key dict: {"root_tag": content}.
    - Attributes are prefixed with "@".
    - Mixed text/children are represented using "#text".
    - Repeated sibling tags become lists.
    - Scalars use simple type inference.
    - When serializing a top-level list, ``root_tag`` is required.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import IO, Any, Dict, List, Optional


def loads(text: str) -> Dict[str, Any]:
    """Parse XML text into the documented Python mapping."""
    root = ET.fromstring(text)
    return {root.tag: _element_to_value(root)}


def dumps(
    data: Any,
    root_tag: Optional[str] = None,
    indent: int = 2,
    xml_declaration: bool = True,
) -> str:
    """Serialize Python data to XML.

    A top-level dict with one key uses that key as the root element. A
    top-level dict with multiple keys uses ``root`` unless ``root_tag`` is
    supplied. A top-level list requires an explicit ``root_tag`` and its
    items are emitted using the singular form of that tag.
    """
    if isinstance(data, list):
        if root_tag is None:
            raise ValueError("root_tag is required when serializing a top-level list")
        # A top-level list needs an item element beneath the root.
        content = {_singularize(root_tag): data}
    elif isinstance(data, dict):
        if not data:
            root_tag = root_tag or "root"
            content = ""
        elif root_tag is None and len(data) == 1:
            root_tag = next(iter(data))
            content = data[root_tag]
        elif root_tag is None:
            root_tag = "root"
            content = data
        elif root_tag in data and len(data) == 1:
            content = data[root_tag]
        else:
            content = data
    else:
        if root_tag is None:
            raise ValueError(
                "root_tag is required when serializing a scalar top-level value"
            )
        content = data

    root = _value_to_element(root_tag, content)
    _indent(root, 0, indent)
    body = ET.tostring(root, encoding="unicode")

    if xml_declaration:
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"
    return body + "\n"


def read(stream: IO[str]) -> Dict[str, Any]:
    return loads(stream.read())


def write(
    data: Any,
    stream: IO[str],
    root_tag: Optional[str] = None,
    indent: int = 2,
    xml_declaration: bool = True,
) -> None:
    stream.write(
        dumps(
            data,
            root_tag=root_tag,
            indent=indent,
            xml_declaration=xml_declaration,
        )
    )


def _element_to_value(element: ET.Element) -> Any:
    children = list(element)
    attributes = {
        f"@{key}": _infer_type(value)
        for key, value in element.attrib.items()
    }
    text = (element.text or "").strip()

    if not children and not attributes:
        return _infer_type(text) if text else ""

    result: Dict[str, Any] = {}
    result.update(attributes)

    if children:
        groups: Dict[str, List[Any]] = {}
        order: List[str] = []

        for child in children:
            if child.tag not in groups:
                groups[child.tag] = []
                order.append(child.tag)
            groups[child.tag].append(_element_to_value(child))

        for tag in order:
            values = groups[tag]
            result[tag] = values[0] if len(values) == 1 else values

    if text:
        result["#text"] = _infer_type(text)

    return result


def _infer_type(value: str) -> Any:
    if value == "":
        return ""

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value


def _value_to_element(tag: str, value: Any) -> ET.Element:
    element = ET.Element(tag)

    if isinstance(value, dict):
        _populate_element(element, value)
    elif isinstance(value, list):
        child_tag = _singularize(tag)
        for item in value:
            if (
                isinstance(item, dict)
                and len(item) == 1
                and next(iter(item)) == child_tag
            ):
                element.append(_value_to_element(child_tag, item[child_tag]))
            else:
                element.append(_value_to_element(child_tag, item))
    elif value is not None:
        element.text = _scalar_to_text(value)

    return element


def _populate_element(element: ET.Element, data: Dict[str, Any]) -> None:
    for key, value in data.items():
        if key.startswith("@"):
            element.set(key[1:], _scalar_to_text(value))

    if "#text" in data:
        element.text = _scalar_to_text(data["#text"])

    for key, value in data.items():
        if key.startswith("@") or key == "#text":
            continue

        if isinstance(value, list):
            child_tag = _singularize(key)
            for item in value:
                if (
                    isinstance(item, dict)
                    and len(item) == 1
                    and next(iter(item)) == child_tag
                ):
                    element.append(_value_to_element(child_tag, item[child_tag]))
                else:
                    element.append(_value_to_element(child_tag, item))
        else:
            element.append(_value_to_element(key, value))


def _singularize(tag: str) -> str:
    """Return a conservative singular form for plural XML container tags."""
    if tag.endswith("ies") and len(tag) > 3:
        return tag[:-3] + "y"
    if tag.endswith(("ses", "xes", "zes", "ches", "shes")) and len(tag) > 3:
        return tag[:-2]
    if tag.endswith("s") and not tag.endswith("ss") and len(tag) > 1:
        return tag[:-1]
    return tag


def _scalar_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _indent(elem: ET.Element, level: int = 0, indent_size: int = 2) -> None:
    if indent_size < 0:
        raise ValueError("indent must be >= 0")

    if not len(elem):
        return

    pad = "\n" + " " * (level * indent_size)
    child_pad = "\n" + " " * ((level + 1) * indent_size)

    if not elem.text or not elem.text.strip():
        elem.text = child_pad

    for index, child in enumerate(elem):
        _indent(child, level + 1, indent_size)
        if not child.tail or not child.tail.strip():
            child.tail = pad if index == len(elem) - 1 else child_pad


__all__ = ["dumps", "loads", "read", "write"]
