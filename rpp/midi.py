"""
MIDI event parser using Lark

Provides loads/load functions to parse MIDI event strings from RPP files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Union, List, IO
from lark import Lark, Token, Tree, Transformer


class MIDIEventType(Enum):
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    OTHER = "other"


@dataclass
class MIDIEvent:
    """MIDI event data structure"""

    type: MIDIEventType
    prefix: str
    delta: str
    status: str
    # 可选字段
    note: str = ""
    velocity: str = ""
    controller: str = ""
    value: str = ""
    byte2: str = ""
    byte3: str = ""


class MIDIEventHandler:
    """Handler for MIDI events in lark_parser.py"""

    # Token transformations
    def NOTE_ON_STATUS(self, token: Token) -> str:
        return token.value

    def NOTE_OFF_STATUS(self, token: Token) -> str:
        return token.value

    def CC_STATUS(self, token: Token) -> str:
        return token.value

    def ANY_STATUS(self, token: Token) -> str:
        return token.value

    def DELTA(self, token: Token) -> str:
        return token.value

    def HEX_BYTE(self, token: Token) -> str:
        return token.value

    def prefix(self, children: List[str]) -> str:
        return children[0] if children else "E"

    def note_on(self, children: List[str]) -> MIDIEvent:
        """Parse note_on event: E delta 9X note velocity"""
        return MIDIEvent(
            type=MIDIEventType.NOTE_ON,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            note=children[3],
            velocity=children[4],
        )

    def note_off(self, children: List[str]) -> MIDIEvent:
        """Parse note_off event: E delta 8X note velocity"""
        return MIDIEvent(
            type=MIDIEventType.NOTE_OFF,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            note=children[3],
            velocity=children[4],
        )

    def control_change(self, children: List[str]) -> MIDIEvent:
        """Parse control_change event: E delta bX controller value"""
        return MIDIEvent(
            type=MIDIEventType.CONTROL_CHANGE,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            controller=children[3],
            value=children[4],
        )

    def other_event(self, children: List[str]) -> MIDIEvent:
        """Parse other MIDI events"""
        return MIDIEvent(
            type=MIDIEventType.OTHER,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            byte2=children[3],
            byte3=children[4],
        )

    def event(self, children: List[MIDIEvent]) -> MIDIEvent:
        """Return the MIDI event"""
        return children[0] if children else None


# Global parser instance
_parser: Lark | None = None


def _get_parser() -> Lark:
    """Get or create the lark parser instance for MIDI"""
    global _parser
    if _parser is None:
        grammar_path = os.path.join(os.path.dirname(__file__), "midi.lark")
        _parser = Lark.open(grammar_path, parser="lalr")
    return _parser


def _is_token(obj) -> bool:
    """Check if object is a Token"""
    return isinstance(obj, Token)


class MIDITransformer(Transformer):
    """Transform Lark parse tree to MIDI event objects"""

    # Token transformations
    def midi__HEX_BYTE(self, token: Token) -> str:
        return token.value

    def midi__HEX_DIGIT(self, token: Token) -> str:
        return token.value

    def midi__DELTA(self, token: Token) -> str:
        return token.value

    def midi__NOTE_ON_STATUS(self, token: Token) -> str:
        return token.value

    def midi__NOTE_OFF_STATUS(self, token: Token) -> str:
        return token.value

    def midi__CC_STATUS(self, token: Token) -> str:
        return token.value

    # Tree transformations
    def midi__prefix(self, children: List[str]) -> str:
        return children[0] if children else "E"

    def midi__note_on(self, children: List[str]) -> MIDIEvent:
        return MIDIEvent(
            type=MIDIEventType.NOTE_ON,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            note=children[3],
            velocity=children[4],
        )

    def midi__note_off(self, children: List[str]) -> MIDIEvent:
        return MIDIEvent(
            type=MIDIEventType.NOTE_OFF,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            note=children[3],
            velocity=children[4],
        )

    def midi__control_change(self, children: List[str]) -> MIDIEvent:
        return MIDIEvent(
            type=MIDIEventType.CONTROL_CHANGE,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            controller=children[3],
            value=children[4],
        )

    def midi__other_event(self, children: List[str]) -> MIDIEvent:
        return MIDIEvent(
            type=MIDIEventType.OTHER,
            prefix=children[0],
            delta=children[1],
            status=children[2],
            byte2=children[3],
            byte3=children[4],
        )

    def midi__event(self, children: List[MIDIEvent]) -> MIDIEvent:
        return children[0] if children else None

    def midi__start(self, children: List[MIDIEvent]) -> List[MIDIEvent]:
        return children


# Create transformer instance
_transformer = MIDITransformer()


def loads(string: str) -> List[MIDIEvent]:
    """Parse MIDI events from string

    Args:
        string: MIDI event string (e.g., "E 3840 90 60 40\nE 0 80 60 00")

    Returns:
        List of MIDIEvent objects
    """
    parser = _get_parser()
    tree = parser.parse(string)
    return _transformer.transform(tree)


def load(fp: IO[str]) -> List[MIDIEvent]:
    """Load MIDI events from file pointer

    Args:
        fp: File pointer to read from

    Returns:
        List of MIDIEvent objects
    """
    return loads(fp.read())


def load_file(path: str) -> List[MIDIEvent]:
    """Load MIDI events from file path

    Args:
        path: Path to MIDI file

    Returns:
        List of MIDIEvent objects
    """
    with open(path, "r") as fp:
        return load(fp)


def _get_token_value(node) -> str:
    """从 Tree 或 Token 中提取值"""
    if isinstance(node, Token):
        return node.value
    if isinstance(node, Tree):
        # Tree 有一个 data 属性表示类型，一个 children 属性表示子节点
        # 对于终端节点，children 通常是 Token 列表
        if node.children:
            # 递归获取第一个子节点的值
            return _get_token_value(node.children[0])
        return ""
    return str(node)


def _get_event_type(status: str) -> MIDIEventType:
    """根据 status 字节判断事件类型

    Args:
        status: 状态字节（如 '90', '80', 'b0'）

    Returns:
        MIDIEventType 枚举值
    """
    if not status:
        return MIDIEventType.OTHER
    status_upper = status.upper()
    if len(status_upper) >= 2:
        first_char = status_upper[0]
        if first_char == "9":
            return MIDIEventType.NOTE_ON
        elif first_char == "8":
            return MIDIEventType.NOTE_OFF
        elif first_char == "B":
            return MIDIEventType.CONTROL_CHANGE
    return MIDIEventType.OTHER


def from_children(children: List) -> MIDIEvent:
    """从 lark_parser 传递的 Tree/Token 列表中解析 MIDI 事件

    Args:
        children: 形如 [Tree('midi__PREFIX', 'E'), Token('midi__DELTA', '3840'),
                      Token('midi__CC_STATUS', 'b0'), Token('midi__HEX_BYTE', '7b'),
                      Token('midi__HEX_BYTE', '00')]

    Returns:
        MIDIEvent 对象
    """
    prefix = ""
    delta = ""
    status = ""
    byte2 = ""
    byte3 = ""

    for node in children:
        if isinstance(node, Tree):
            token_type = node.data  # 如 'midi__PREFIX', 'midi__DELTA' 等
            value = _get_token_value(node)
        elif isinstance(node, Token):
            token_type = node.type  # 如 'midi__DELTA', 'midi__CC_STATUS' 等
            value = node.value
        else:
            continue

        # 根据 token 类型赋值
        if token_type in ("midi__PREFIX", "PREFIX"):
            prefix = value
        elif token_type in ("midi__DELTA", "DELTA"):
            delta = value
        elif token_type in (
            "midi__NOTE_ON_STATUS",
            "NOTE_ON_STATUS",
            "midi__NOTE_OFF_STATUS",
            "NOTE_OFF_STATUS",
            "midi__CC_STATUS",
            "CC_STATUS",
            "midi__ANY_STATUS",
            "ANY_STATUS",
        ):
            status = value
        elif token_type in ("midi__HEX_BYTE", "HEX_BYTE"):
            if not byte2:
                byte2 = value
            elif not byte3:
                byte3 = value

    # 根据 status 判断事件类型
    event_type = _get_event_type(status)

    # 根据事件类型设置对应字段
    if event_type == MIDIEventType.NOTE_ON:
        return MIDIEvent(
            type=event_type,
            prefix=prefix,
            delta=delta,
            status=status,
            note=byte2,
            velocity=byte3,
        )
    elif event_type == MIDIEventType.NOTE_OFF:
        return MIDIEvent(
            type=event_type,
            prefix=prefix,
            delta=delta,
            status=status,
            note=byte2,
            velocity=byte3,
        )
    elif event_type == MIDIEventType.CONTROL_CHANGE:
        return MIDIEvent(
            type=event_type,
            prefix=prefix,
            delta=delta,
            status=status,
            controller=byte2,
            value=byte3,
        )
    else:
        return MIDIEvent(
            type=event_type,
            prefix=prefix,
            delta=delta,
            status=status,
            byte2=byte2,
            byte3=byte3,
        )

