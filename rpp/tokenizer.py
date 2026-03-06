"""RPP tokenizer module.

Provides tokenization functionality for RPP file format.
"""

from __future__ import annotations

import re
from typing import Iterator, Callable

from lark import Token


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

# Token type lookup table based on value patterns
_TOKEN_TYPE_RESOLVERS: list[tuple[Callable[[str], bool], str]] = [
    (lambda v: v == "<", "LESSTHAN"),
    (lambda v: v == ">", "MORETHAN"),
    (lambda v: len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"), "ESCAPED_STRING"),
    (lambda v: len(v) >= 2 and v[0] == "`" and v[-1] == "`", "BACKQUOTED_NAME"),
    (lambda v: v == "\n", "NEWLINE"),
    (lambda v: not v.strip(), "WHITESPACE"),
]

# Default token type
_DEFAULT_TOKEN_TYPE = "UNQUOTED"


def _resolve_token_type(value: str) -> str:
    """Resolve token type based on value patterns.

    Args:
        value: The token value to classify.

    Returns:
        The token type string.
    """
    for predicate, token_type in _TOKEN_TYPE_RESOLVERS:
        if predicate(value):
            return token_type
    return _DEFAULT_TOKEN_TYPE


def _strip_quotes(value: str) -> str:
    """Strip surrounding quotes from a string value.

    Args:
        value: The string that may have quotes.

    Returns:
        The string without surrounding quotes.
    """
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'", "`"):
        return value[1:-1]
    return value


def _process_token_value(value: str, token_type: str) -> tuple[str, str]:
    """Process token value based on its type.

    Args:
        value: The raw token value.
        token_type: The resolved token type.

    Returns:
        Tuple of (processed_value, final_token_type).
    """
    if token_type in ("ESCAPED_STRING", "BACKQUOTED_NAME"):
        return _strip_quotes(value), token_type
    return value, token_type


def tokenize(string: str) -> Iterator[Token]:
    """Tokenize RPP content.

    Args:
        string: RPP content to tokenize.

    Yields:
        Token objects with type, value, and position.
    """
    pos = 0
    length = len(string)

    while pos < length:
        match = _TOKEN_PATTERN.match(string, pos)

        if not match:
            pos += 1
            continue

        # Get the first non-empty group
        value = next((g for g in match.groups() if g), None)

        if value is None:
            pos = match.end()
            continue

        # Resolve token type and process value
        token_type = _resolve_token_type(value)
        processed_value, final_type = _process_token_value(value, token_type)

        # Skip whitespace tokens
        if final_type != "WHITESPACE":
            yield Token(final_type, processed_value, pos)

        pos = match.end()

    # Always add a trailing newline token
    yield Token("NEWLINE", "\n", pos)
