from ply import yacc
from typing import cast

from .element import Element
from .scanner import LexToken, tokens  # noqa


def parser() -> yacc.LRParser:
    yacc_tree = yacc.yacc(optimize=True, debug=False, write_tables=False)
    return cast(yacc.LRParser, yacc_tree)


def p_tree(t):
    """tree : OPEN root CLOSE NEWLINE
    | OPEN root items CLOSE NEWLINE"""
    t[0] = t[2]
    if len(t) > 5:
        t[0].extend(t[3])


def p_root(t):
    """root : list NEWLINE"""
    t[0] = Element(t[1][0], children=[])
    if len(t) > 2:
        t[0].attrib = t[1][1:]


def p_items(t):
    """items : item
    | item items"""
    if t[0] is None:
        t[0] = []
    t[0].append(t[1])
    if len(t) > 2:
        t[0] += t[2]


def p_item_list(t):
    """item : list NEWLINE"""
    if len(t[1]) == 1:
        t[0] = t[1][0]
    else:
        t[0] = t[1]


def p_item_tree(t):
    """item : tree"""
    t[0] = t[1]


def p_list(t):
    """list : STRING
    | STRING list"""
    if t[0] is None:
        t[0] = []
    t[0].append(t[1])
    if len(t) > 2:
        t[0] += t[2]


def p_error(t: LexToken | None):
    if t is None:
        message = "syntax error at EOF"
    else:
        message = f"syntax error at line {t.lineno or 1}, token={t.type}"
    raise ValueError(message)
