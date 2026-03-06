"""RPP is a format used to describe `REAPER <http://reaper.fm>`_
projects."""

from .element import Element
from .rpp import dump, dumps, loads, load
from .tokenizer import tokenize


__version__ = "0.6"
__author__ = "Sviatoslav Abakumov <dust.harvesting@gmail.com>"
__all__ = ["dump", "dumps", "load", "loads", "Element", "tokenize"]

