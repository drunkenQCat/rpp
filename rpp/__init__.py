r"""RPP is a format used to describe REAPER <http://reaper.fm> projects."""

from .scanner import Symbol
from .decoder import yacc  # noqa
from .encoder import encode  # noqa
from .helpers import findall, find, update  # noqa


__version__ = '0.1'
__all__ = ['dump', 'dumps', 'load', 'loads', 'RPP', 'Symbol']
__author__ = 'Sviatoslav Abakumov <dust.harvesting@gmail.com>'


def loads(string):
    return yacc.parse(string)


def load(fp):
    return loads(fp.read())


def dumps(lists, indent=2):
    return encode(lists, indent=indent)


def dump(lists, fp, indent=2):
    fp.write(dumps(lists, indent))
