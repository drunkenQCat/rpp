"""RPP parser public API.

This module provides the public API for parsing and generating RPP files.
The actual parsing is done by lark_parser.py using the Lark grammar.
"""

from __future__ import annotations

from typing import List, TextIO, Union

from lark import Token

from .element import Element
from .lark_parser import loads as _lark_loads, load as _lark_load
from .encoder import encode
from .tokenizer import tokenize as _tokenize


def tokenize(string: str) -> list[Token]:
    """Tokenize RPP content.

    Args:
        string: RPP content to tokenize.

    Returns:
        List of Token objects.
    """
    return list(_tokenize(string))


def loads(string: str) -> Element:
    """Load RPP content from string.

    Args:
        string: RPP content to parse.

    Returns:
        Root Element of the parsed RPP structure.
    """
    return _lark_loads(string)


def load(fp: TextIO) -> Element:
    """Load RPP content from file pointer.

    Args:
        fp: File pointer to read from.

    Returns:
        Root Element of the parsed RPP structure.
    """
    return _lark_load(fp)


def dumps(lists: Union[Element, List[Element]], indent: int = 2) -> str:
    """Dump RPP content to string.

    Args:
        lists: Element or list of Elements to serialize.
        indent: Number of spaces per indentation level.

    Returns:
        Serialized RPP string.
    """
    return encode(lists, indent=indent)


def dump(lists: Union[Element, List[Element]], fp: TextIO, indent: int = 2) -> None:
    """Dump RPP content to file pointer.

    Args:
        lists: Element or list of Elements to serialize.
        fp: File pointer to write to.
        indent: Number of spaces per indentation level.
    """
    fp.write(dumps(lists, indent))
