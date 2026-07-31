import xml.etree.ElementTree as ET


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(parent: ET.Element, child_name: str) -> str:
    for child in parent:
        if local_name(child.tag) == child_name:
            return child.text.strip() if child.text else ""
    return ""


def find_text(parent: ET.Element, child_name: str) -> str:
    for child in parent.iter():
        if local_name(child.tag) == child_name:
            return child.text.strip() if child.text else ""
    return ""


def find_child(parent: ET.Element, child_name: str) -> ET.Element | None:
    for child in parent:
        if local_name(child.tag) == child_name:
            return child
    return None


def to_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    return None


def to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
