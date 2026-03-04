from __future__ import annotations

from collections.abc import Iterable
from typing import Union

from .element import Element


def encode(element: Union[Element, str, list], indent: int = 2, level: int = 0) -> str:
    result = " " * level * indent
    if isinstance(element, Element):
        result += "<"
        result += encode_tag_and_attrib(element)
        for item in element:
            result += encode(item, level=level + 1)
        result += " " * level * indent + ">\n"
    elif isinstance(element, str):
        result += quote_string(element, quote_pipe=False) + "\n"
    else:
        result += encode_value(element) + "\n"
    return result


def encode_tag_and_attrib(element: Element) -> str:
    result = element.tag
    if element.attrib:
        result += " " + encode_iterable(element.attrib)
    result += "\n"
    return result


def encode_value(value: Union[str, Iterable, object]) -> str:
    if isinstance(value, str):
        return quote_string(value)
    elif isinstance(value, Iterable):
        return encode_iterable(value)
    else:
        return quote_string(str(value))


def encode_iterable(iterable: Iterable) -> str:
    return " ".join(map(encode_value, iterable))


def quote_string(value: str, quote_pipe: bool = True) -> str:
    if not value:
        return '""'
    if not should_quote(value, quote_pipe):
        return value
    quote, quoted_value = quote_mark(value)
    return f"{quote}{quoted_value}{quote}"


def should_quote(s: str, quote_pipe: bool) -> bool:
    # 如果字符串包含 ::，说明是扩展行，不需要引号
    if "::" in s:
        return False
    return (quote_pipe or not starts_with_pipe(s)) and (
        starts_with_quote(s) or has_whitespace(s)
    )


def has_whitespace(s: str) -> bool:
    whitespace = " \t"
    return any(ch in whitespace for ch in s)


def quote_mark(s: str) -> tuple[str, str]:
    quote = '"'
    value = s
    if '"' in s:
        quote = "'"
    if "'" in s:
        quote = "`"
    if "`" in s:
        quote = "`"
        value = s.replace("`", "'")
    return quote, value


def starts_with_quote(s: str) -> bool:
    quotes = "\"'`"
    return len(s) > 0 and s[0] in quotes


def starts_with_pipe(s: str) -> bool:
    return len(s) > 0 and s[0] == "|"

