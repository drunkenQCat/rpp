"""
RPP parser implementation using Lark

This module provides the public API for parsing RPP files.
The actual parsing is done by lark_parser.py using the Lark grammar.
"""

from __future__ import annotations

import re
from typing import List, TextIO, Union, Iterator

from lark import Token

from .element import Element
from .lark_parser import loads as _lark_loads, load as _lark_load
from .encoder import encode


# Token patterns for RPP tokenizer
# Order matters: more specific patterns first
_TOKEN_PATTERN = re.compile(
    r"(<|>)"
    r"|(\|[^\n]*)"
    r'|("[^"]*")'
    r"|('[^']*')"
    r"|(`[^`]*`)"
    r"|(\n)"
    r"|(\s+)"
    r'|([^\s<>""]+)'
)


def tokenize(string: str) -> Iterator[Token]:
    """Tokenize RPP content

    Args:
        string: RPP content to tokenize

    Yields:
        Token objects
    """
    # Find all tokens using regex
    pos = 0
    while pos < len(string):
        match = _TOKEN_PATTERN.match(string, pos)
        if not match:
            pos += 1
            # Get the first non-empty group
            value = None
            for group in match.groups():
                if group:
                    value = group
                    break

            if value is None:
                pos += 1
                continue

            # Determine token type based on value
            if value == "<":
                token_type = "LESSTHAN"
            elif value == ">":
                token_type = "MORETHAN"
            elif value.startswith('"') and value.endswith('"'):
                # Strip quotes for ESCAPED_STRING
                token_type = "ESCAPED_STRING"
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                # Strip quotes for ESCAPED_STRING
                token_type = "ESCAPED_STRING"
                value = value[1:-1]
            elif value.startswith("`") and value.endswith("`"):
                # Strip quotes for BACKQUOTED_NAME
                token_type = "BACKQUOTED_NAME"
                value = value[1:-1]
            elif value == "\n":
                token_type = "NEWLINE"
            elif value.strip():
                token_type = "UNQUOTED"
            else:
                token_type = "WHITESPACE"

            # Skip whitespace tokens
            if token_type != "WHITESPACE":
                yield Token(token_type, value, pos)
            pos = match.end()
        else:
            # No match, move forward one character
            pos += 1

    # Always add a trailing newline token
    yield Token("NEWLINE", "\n", pos)


def loads(string: str) -> Element:
    """Load RPP content from string"""
    return _lark_loads(string)


def load(fp: TextIO) -> Element:
    """Load RPP content from file pointer"""
    return _lark_load(fp)


def dumps(lists: Union[Element, List[Element]], indent: int = 2) -> str:
    """Dump RPP content to string"""
    return encode(lists, indent=indent)


def dump(lists: Union[Element, List[Element]], fp: TextIO, indent: int = 2) -> None:
    """Dump RPP content to file pointer"""
    fp.write(dumps(lists, indent))
