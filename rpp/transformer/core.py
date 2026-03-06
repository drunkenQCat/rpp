"""Core RPP transformer implementation.

Provides RPPTransformer class that converts Lark parse trees to Element objects.
"""

from __future__ import annotations

import os
from typing import Union, List, IO
from lark import Lark, Token, Tree, Transformer, v_args

from ..element import Element
from . import midi
from ..models.grammar import PendingFloat
from .utils import strip_quotes, is_token, merge_split_values, merge_pending_floats
from .handlers import (
    handle_element_children,
    handle_struct_as_content,
    handle_attr_list,
    handle_content_lines,
)

# Type aliases
_ChildType = Union[str, List[str], Element]

# Global parser instance
_parser: Lark | None = None


def get_parser() -> Lark:
    """Get or create the Lark parser instance.

    Returns:
        Configured Lark parser for RPP grammar.
    """
    global _parser
    if _parser is None:
        grammar_path = os.path.join(
            os.path.dirname(__file__), "..", "grammars", "rpp.lark"
        )
        _parser = Lark.open(grammar_path, parser="earley")
    return _parser


class RPPTransformer(Transformer):
    """Transform Lark parse tree to Element objects.

    In Lark Transformer:
    - Token methods (uppercase) receive the Token object directly
    - Tree methods (lowercase) receive a list of transformed children
    """

    # Token transformations - receive Token object directly
    def TAG(self, token: Token) -> str:
        return token.value

    def SIGNED_FLOAT(self, token: Token) -> str:
        return token.value

    def SIGNED_INT(self, token: Token) -> str:
        return token.value

    def ESCAPED_STRING(self, token: Token) -> str:
        return strip_quotes(token.value)

    def UNQUOTED(self, token: Token) -> str:
        return token.value

    def SINGLE_QUOTED_STR(self, token: Token) -> str:
        return strip_quotes(token.value)

    def NOTE(self, token: Token) -> str:
        return token.value

    def BASE64_GROUP(self, token: Token) -> str:
        return token.value

    def HEX_NUMBER(self, token: Token) -> str:
        return token.value

    def HEADLESS_HEX_NUMBER(self, token: Token) -> str:
        return token.value

    def BACKQUOTED_NAME(self, token: Token) -> str:
        return strip_quotes(token.value)

    def UNQUOTED_NAME(self, token: Token) -> str:
        return token.value

    # Simple tree transformations
    def string(self, children: List[str]) -> str:
        return children[0]

    def empty_string(self, children: List[str]) -> str:
        return ""

    def js_float_num(self, children: List[str]) -> str:
        return children[0]

    def int_num(self, children: List[str]) -> str:
        return children[0]

    def float_num(self, children: List[str]) -> PendingFloat:
        pending_value = children[0]
        if pending_value.startswith("."):
            return PendingFloat(False, pending_value)
        return PendingFloat(True, pending_value)

    def unquoted(self, children: List[str]) -> str:
        return children[0]

    def single_quoted_string(self, children: List[str]) -> str:
        return children[0]

    def dynamic_link(self, children: List[str]) -> str:
        return f"{children[0]}.{children[1]}"

    def js_fx_name(self, children: List[str]) -> str:
        return f"{children[0]}/{children[1]}"

    def pattern(self, children: List[str]) -> str:
        return f"${children[0]}"

    def guid(self, children: List[str]) -> str:
        return f"{{{children[0]}}}"

    def aux_info(self, children: List[str]) -> str:
        return f"{children[0]}:{children[1]}"

    def parmenv_info(self, children: List[str]) -> str:
        return f"{children[0]}:{children[1]}"

    def vst_quoted_string(self, children: List[str]) -> str:
        return f"{children[0]}<{children[1]}>"

    def empty_param(self, children: List[str]) -> str:
        return "-"

    def struct(self, children: List) -> List:
        return children

    def tag(self, children: List[str]) -> str:
        return children[0]

    def attr_list(self, children: List) -> List:
        return handle_attr_list(children)

    def content(self, children: List) -> _ChildType | None:
        if not children:
            return None
        val = children[0]
        # If it's a list (from compressed), pass through directly
        if isinstance(val, list):
            return val
        return val

    def content_lines(self, children: List) -> List:
        return handle_content_lines(children)

    def element(self, children: List) -> Element:
        """Transform element rule to Element object."""
        # Find struct in children (skip OPEN, NEWLINE, CLOSE tokens)
        struct = self._find_struct(children)
        if struct is None:
            raise ValueError("Expected struct in element")

        tag = struct[0]
        attrib = [str(p) for p in struct[1]]
        result_children = handle_element_children(children, tag)

        return Element(tag=tag, attrib=tuple(attrib), children=result_children)

    def _find_struct(self, children: List) -> List | None:
        """Find struct in element children."""
        for child in children:
            if isinstance(child, list) and len(child) >= 2:
                return child
        return None

    def struct_as_content(self, children: List) -> List[str]:
        """Handle struct as content (not inside element)."""
        return handle_struct_as_content(children)

    def full_groups(self, children: List[str]) -> str:
        return "".join(children)

    def padding(self, children: List[str]) -> str:
        return "".join(children)

    def compressed(self, children: List) -> str:
        return children[0]

    def base64_string(self, children: List) -> str:
        return "".join(str(c) for c in children if not is_token(c))

    def name_field(self, children: List[str]) -> List[str]:
        value = children[0] if children else ""
        return ["NAME", strip_quotes(value)]

    def name_value(self, children: List[str]) -> str:
        return children[0]

    def js_parameter_list(self, children: List) -> List[str]:
        return [str(c) for c in children]

    def ext_line(self, children: List) -> str:
        if children:
            return str(children[0]).strip()
        return ""

    def note_line(self, children: List[str]) -> str:
        return children[0]

    def keysig(self, children: List[str]) -> List[str]:
        return children

    def auto_color(self, children: List) -> List[str]:
        result: List[str] = [f"{{{children[0]}}}", str(children[1])]
        for i in range(2, 5):
            result.append(str(children[i]))
        return result

    def string_in_quotes(self, children: List[str]) -> str:
        return children[0]

    def midi_event(self, children: List) -> List[str]:
        """Transform midi_event to list representation."""
        if not children:
            return []

        try:
            event = midi.from_children(children)
            return [
                event.prefix,
                event.delta,
                event.status,
                event.byte2 or event.note or event.controller,
                event.byte3 or event.velocity or event.value,
            ]
        except Exception:
            return []


# Create transformer instance
_transformer = RPPTransformer()


def loads(string: str) -> Element:
    """Parse RPP content from string using Lark parser."""
    parser = get_parser()
    tree = parser.parse(string)
    return _transformer.transform(tree)


def load(fp: IO[str]) -> Element:
    """Load RPP content from file pointer."""
    return loads(fp.read())
