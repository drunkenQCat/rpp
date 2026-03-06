"""Lark-based RPP parser implementation.

This module re-exports functionality from the transformer package
for backward compatibility.
"""

from __future__ import annotations

from typing import IO

from .element import Element
from .transformer import loads as _loads, load as _load, get_parser

# Re-export for backward compatibility
__all__ = ["loads", "load", "get_parser"]


def loads(string: str) -> Element:
    """Parse RPP content from string using Lark parser."""
    return _loads(string)


def load(fp: IO[str]) -> Element:
    """Load RPP content from file pointer."""
    return _load(fp)
