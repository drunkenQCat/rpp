"""Utility functions for RPP transformer.

Provides helper functions for quote stripping, token checking, and value merging.
"""

from __future__ import annotations

from lark import Token

from ..models.grammar import PendingFloat


def strip_quotes(value: str) -> str:
    """Strip surrounding quotes from a string value.

    Args:
        value: The string that may have quotes.

    Returns:
        The string without surrounding quotes.
    """
    if len(value) >= 2:
        if (
            (value[0] == '"' and value[-1] == '"')
            or (value[0] == "'" and value[-1] == "'")
            or (value[0] == "`" and value[-1] == "`")
        ):
            return value[1:-1]
    return value


def is_token(obj) -> bool:
    """Check if object is a Lark Token.

    Args:
        obj: The object to check.

    Returns:
        True if obj is a Token, False otherwise.
    """
    return isinstance(obj, Token)


def merge_split_values(attrs: list) -> list:
    """Merge values that were incorrectly split by the parser.

    Handles cases like:
    - RENDER_1X (RENDER_ + 1 + X)
    - SELECTION2 (SELECTION + 2)
    - 5.50c (5.50 + c)

    Args:
        attrs: List of attribute values.

    Returns:
        List with merged values.
    """
    if not attrs:
        return attrs

    result = []
    i = 0
    while i < len(attrs):
        current = str(attrs[i])

        # Case 1: TAG ends with _, followed by digit and optional uppercase
        # e.g., RENDER_ + 1 + X -> RENDER_1X
        if current.endswith("_") and i + 1 < len(attrs):
            next_val = str(attrs[i + 1])
            if next_val and next_val[0].isdigit():
                merged = current + next_val
                if i + 2 < len(attrs):
                    third_val = str(attrs[i + 2])
                    if third_val and third_val.isupper() and len(third_val) <= 4:
                        merged += third_val
                        i += 3
                    else:
                        i += 2
                else:
                    i += 2
                result.append(merged)
                continue

        # Case 2: SELECTION + multi-digit number -> SELECTION2
        if current == "SELECTION" and i + 1 < len(attrs):
            next_val = str(attrs[i + 1])
            if next_val and len(next_val) >= 2 and next_val.isdigit():
                merged = current + next_val
                i += 2
                result.append(merged)
                continue

        # Case 3: Version numbers like 5.50c (number + lowercase letter)
        if i + 1 < len(attrs):
            next_val = str(attrs[i + 1])
            if (
                next_val
                and len(next_val) == 1
                and next_val.islower()
                and next_val.isalpha()
            ):
                merged = current + next_val
                i += 2
                result.append(merged)
                continue

        result.append(current)
        i += 1

    return result


def merge_pending_floats(attrs: list) -> list:
    """Merge PendingFloat values with preceding integers.

    Handles cases like -0 + .0005 -> -0.0005

    Args:
        attrs: List of attribute values.

    Returns:
        List with merged float values.
    """
    result = []
    for attr in attrs:
        if isinstance(attr, PendingFloat) and not attr.is_real_float and result:
            prev = result[-1]
            if isinstance(prev, str) and (
                prev.isdigit() or prev.startswith("-") or prev.lstrip("-").isdigit()
            ):
                merged = prev + attr.value
                result[-1] = merged
                continue
        result.append(attr)
    return result
