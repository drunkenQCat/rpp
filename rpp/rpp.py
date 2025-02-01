from typing import cast

from rpp.element import Element
from . import scanner
from .decoder import parser
from .encoder import encode


def loads(string: str):
    lexer = scanner.lexer()
    yacc = parser()

    return cast(Element | None, yacc.parse(string, lexer))


def load(fp):
    return loads(fp.read())


def dumps(lists, indent=2):
    return encode(lists, indent=indent)


def dump(lists, fp, indent=2):
    fp.write(dumps(lists, indent))
