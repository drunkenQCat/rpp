"""
Lark-based RPP parser implementation

Uses lark Transformer to convert parse tree to Element objects.
"""

from __future__ import annotations

import os
from typing import Union, List, IO
from lark import Lark, Token, Tree, Transformer, v_args

from .element import Element
from . import midi
from .models.grammar import PendingFloat


# Type aliases
_ChildType = Union[str, List[str], Element]


# Global parser instance
_parser: Lark | None = None


def _get_parser() -> Lark:
    """Get or create the lark parser instance"""
    global _parser
    if _parser is None:
        grammar_path = os.path.join(os.path.dirname(__file__), "rpp.lark")
        _parser = Lark.open(grammar_path, parser="earley")
    return _parser


def _strip_quotes(value: str) -> str:
    """Strip quotes from a string value"""
    if len(value) >= 2:
        if (
            (value[0] == '"' and value[-1] == '"')
            or (value[0] == "'" and value[-1] == "'")
            or (value[0] == "`" and value[-1] == "`")
        ):
            return value[1:-1]
    return value


def _is_token(obj) -> bool:
    """Check if object is a Token"""
    return isinstance(obj, Token)


class RPPTransformer(Transformer):
    """Transform Lark parse tree to Element objects

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
        return _strip_quotes(token.value)

    def UNQUOTED(self, token: Token) -> str:
        return token.value

    def SINGLE_QUOTED_STR(self, token: Token) -> str:
        return _strip_quotes(token.value)

    def NOTE(self, token: Token) -> str:
        return token.value

    def BASE64_GROUP(self, token: Token) -> str:
        return token.value

    def HEX_NUMBER(self, token: Token) -> str:
        return token.value

    def HEADLESS_HEX_NUMBER(self, token: Token) -> str:
        return token.value

    def BACKQUOTED_NAME(self, token: Token) -> str:
        return _strip_quotes(token.value)

    def UNQUOTED_NAME(self, token: Token) -> str:
        return token.value

    # Tree transformations - receive list of transformed children
    def string(self, children: List[str]) -> str:
        return children[0]

    def empty_string(self, children: List[str]) -> str:
        return ""

    def js_float_num(self, children: List[str]) -> str:
        return children[0]

    def int_num(self, children: List[str]) -> str:
        # 返回字符串以保留原始格式（如 -0）
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

    def element(self, children: List) -> Element:
        # children: [OPEN, struct, NEWLINE, content_lines, CLOSE, NEWLINE?]
        # struct is [tag, attr_list]

        # DEBUG
        import os
        if os.environ.get('DEBUG_ELEMENT'):
            print(f"DEBUG element: children = {children}")

        # Find struct in children (skip OPEN, NEWLINE, CLOSE tokens)
        struct: List | None = None
        for child in children:
            if isinstance(child, list) and len(child) >= 2:
                # This is struct: [tag, attr_list]
                struct = child
                break

        if struct is None:
            raise ValueError("Expected struct in element")

        tag = struct[0]
        attr_list = struct[1]
        attrib: List[str] = [str(p) for p in attr_list]

        # Get content (everything after struct, skip tokens)
        result_children: List[_ChildType] = []
        for child in children:
            # Skip tokens
            if _is_token(child):
                continue
            # Skip struct and empty lists
            if not isinstance(child, list) or len(child) == 0:
                continue
            # Skip struct (compare first element)
            if child[0] == tag:
                continue
            # If child is a list (content_lines), we need to check its contents
            # content_lines returns a list of contents, each content could be:
            # - a string (for simple content)
            # - a list (for struct_content or compressed)
            # - an Element (for nested element)
            if child and isinstance(child, list):
                # Check if this is a list of contents (from content_lines)
                # Each content could be a string, list, or Element
                for content_item in child:
                    if isinstance(content_item, list):
                        # This could be struct_content or compressed result
                        # If it's a list of strings (like from compressed), append the whole list
                        # Otherwise, append the content_item
                        if content_item and isinstance(content_item[0], str):
                            # Check if it looks like struct_content (first element is a tag)
                            # struct_content: [TAG, attr1, attr2, ...]
                            # compressed: [base64_str1, base64_str2, ...]
                            # We can distinguish by checking if first element is uppercase
                            if content_item[0].isupper() and len(content_item) > 1:
                                # This is struct_content
                                result_children.append(content_item)
                            else:
                                # This is compressed result
                                result_children.append(content_item)
                        else:
                            result_children.append(content_item)
                    else:
                        result_children.append(content_item)
            else:
                result_children.append(child)

        return Element(tag=tag, attrib=tuple(attrib), children=result_children)

    def struct(self, children: List) -> List:
        return children

    def tag(self, children: List[str]) -> str:
        return children[0]

    def attr_list(self, children: List) -> List:
        result = []
        for child in children:
            if result and isinstance(child, PendingFloat) and not child.is_real_float:
                # 检查前一个是否是字符串（来自 int_num）且以数字或 - 开头
                prev = result[-1]
                if isinstance(prev, str) and (prev.isdigit() or prev.startswith('-')):
                    # 合并：prev + child.value
                    merged = prev + child.value
                    result[-1] = merged  # 替换前一个
                    continue  # 跳过当前
            result.append(child)

        # 后处理：合并被错误拆分的值
        result = self._merge_split_values(result)
        # TODO:先不区分，之后再说
        result = [str(c) for c in result]
        return result

    def _merge_split_values(self, attrs: List) -> List:
        """合并被错误拆分的值，如 RENDER_1X, SELECTION2, 5.50c"""
        if not attrs:
            return attrs

        result = []
        i = 0
        while i < len(attrs):
            current = str(attrs[i])

            # 情况1: TAG 以 _ 结尾，后面跟着数字和可选的大写字母
            # 如 RENDER_ + 1 + X -> RENDER_1X
            if current.endswith('_') and i + 1 < len(attrs):
                next_val = str(attrs[i + 1])
                # 检查下一个是否是数字开头
                if next_val and next_val[0].isdigit():
                    merged = current + next_val
                    # 如果还有第三个元素且是大写字母，继续合并
                    if i + 2 < len(attrs):
                        third_val = str(attrs[i + 2])
                        if third_val and third_val.isupper() and len(third_val) <= 4:
                            merged += third_val
                            i += 3  # 跳过3个元素
                        else:
                            i += 2  # 跳过2个元素
                    else:
                        i += 2
                    result.append(merged)
                    continue

            # 情况2: SELECTION + 数字 -> SELECTION2
            # 检查当前是否是 SELECTION，后面跟着数字（只合并两位数，如 SELECTION2）
            if current == 'SELECTION' and i + 1 < len(attrs):
                next_val = str(attrs[i + 1])
                # 只合并两位数的数字，如 SELECTION2
                if next_val and len(next_val) >= 2 and next_val.isdigit():
                    merged = current + next_val
                    i += 2
                    result.append(merged)
                    continue

            # 情况3: 版本号如 5.50c - 数字 + . + 数字 + 小写字母
            # 检查当前是否是数字或带小数的数字，后面跟着小写字母
            if i + 1 < len(attrs):
                next_val = str(attrs[i + 1])
                # 检查是否是数字开头 + 小写字母的模式
                if next_val and len(next_val) == 1 and next_val.islower() and next_val.isalpha():
                    # 合并 current + next_val
                    merged = current + next_val
                    i += 2
                    result.append(merged)
                    continue

            result.append(current)
            i += 1

        return result

    # Handle struct as content (not inside element)
    def struct_as_content(self, children: List) -> List[str]:
        # children: [tag_tree, attr_list_tree]
        # tag_tree is a string (already transformed by tag method)
        # attr_list_tree is a list of parameters
        tag = children[0]
        attr_list = children[1]

        # 特殊处理：如果 tag 以 _ 结尾，后面跟着数字和可选的大写字母
        # 如 RENDER_ + 1 + X -> RENDER_1X
        if tag.endswith('_') and len(attr_list) >= 2:
            first_attr = str(attr_list[0])
            if first_attr.isdigit():
                merged = tag + first_attr
                # 如果还有第二个属性且是大写字母（短单词），继续合并
                if len(attr_list) >= 2:
                    second_attr = str(attr_list[1])
                    if second_attr.isupper() and len(second_attr) <= 4:
                        merged += second_attr
                        # 跳过前3个元素，只保留剩余的属性
                        attr_list = list(attr_list[2:])
                        tag = merged  # 更新 tag
                    else:
                        # 跳过前2个元素，只保留剩余的属性
                        attr_list = list(attr_list[1:])
                        tag = merged  # 更新 tag
                else:
                    attr_list = []
                    tag = merged  # 更新 tag

        # 特殊处理：SELECTION + 多位数字 -> SELECTION2
        # 注意：只合并多位数字（如 SELECTION2），不合并单个数字（如 SELECTION 0 0）
        if tag == 'SELECTION' and len(attr_list) >= 1:
            first_attr = str(attr_list[0])
            if first_attr.isdigit() and len(first_attr) >= 2:
                merged = tag + first_attr
                # 跳过第1个元素，只保留剩余的属性
                attr_list = list(attr_list[1:])
                tag = merged  # 更新 tag

        # 先合并 PendingFloat（如 -0 + .0005 -> -0.0005）
        result = []
        for i, attr in enumerate(attr_list):
            if isinstance(attr, PendingFloat) and not attr.is_real_float and result:
                prev = result[-1]
                if isinstance(prev, str) and (prev.isdigit() or prev.startswith('-') or prev.lstrip('-').isdigit()):
                    merged = prev + attr.value
                    result[-1] = merged
                    continue
            result.append(attr)
        attr_list = result

        # 合并被错误拆分的值（如 SELECTION2），但跳过已经是合并后的情况
        # 检查是否需要跳过：如果 tag 已经在 attr_list 中出现了，则跳过
        if tag not in attr_list:
            attr_list = self._merge_split_values(attr_list)

        result: List[str] = [tag]
        for param in attr_list:
            result.append(str(param))
        return result

    def content(self, children: List) -> _ChildType | None:
        if not children:
            return None

        val = children[0]

        # 核心修正：如果是 List（即来自 compressed），直接透传
        # 这样父级接收到的就是 ['base64_1', 'base64_2']
        # 而不是 [['base64_1', 'base64_2']]
        if isinstance(val, list):
            return val

        return val

    def content_lines(self, children: List) -> List:
        # children: [content, NEWLINE, content, NEWLINE, ...]
        # We want to extract just the content (skip NEWLINE tokens)
        # Each content item should be a separate element in the result
        import os
        if os.environ.get('DEBUG_CONTENT'):
            print(f"DEBUG content_lines: children = {children}")
        result: List = []
        i = 0
        while i < len(children):
            item = children[i]
            if not _is_token(item):
                # This is content - add as a separate element
                # If item is a list (like from compressed), we need to check its contents
                if isinstance(item, list):
                    # Check if this is a list of strings (from compressed)
                    # If so, we should wrap it in another list
                    if item and isinstance(item[0], str) and not item[0].isupper():
                        # This is compressed result - wrap in a list
                        result.append(item)
                    else:
                        result.append(item)
                else:
                    result.append(item)
            i += 1
        return result

    # 辅助方法：递归提取 Tree 或 Token 中的文本内容
    def _extract_text(self, node):
        if isinstance(node, Token):
            return str(node)
        if isinstance(node, Tree):
            # 递归合并所有子节点，包括那些没有命名的字符串常量
            return "".join(self._extract_text(c) for c in node.children)
        return str(node)

    def full_groups(self, children):
        # 将所有 BASE64_GROUP 连接起来
        return "".join(map(str, children))

    def padding(self, children):
        # 此时 children 可能只有 BASE64_CHAR，因为 "=" 被忽略了
        # 技巧：直接获取原始文本（如果你的 parser 允许）或在语法中保留 "="
        return "".join(map(str, children))

    def compressed(self, children):
        return children[0]

    def base64_string(self, children):
        # 此时 children 已经是处理好的字符串列表了
        # 关键：手动检查原始文本补回 "="，或者在语法中使用 PADDING 终端
        # 这里演示一个最稳妥的方法：直接获取该节点的完整原始文本
        return "".join(str(c) for c in children if not _is_token(c))

    def name_field(self, children: List[str]) -> List[str]:
        value = children[0] if children else ""
        return ["NAME", _strip_quotes(value)]

    def name_value(self, children: List[str]) -> str:
        return children[0]

    def js_parameter_list(self, children: List) -> List[str]:
        return [str(c) for c in children]

    def ext_line(self, children: List) -> str:
        # ext_line: /[A-Za-z0-9_ ]+::[A-Za-z0-9_ :]+/
        # 返回匹配的整行字符串，去除前导空格
        if children:
            return str(children[0]).strip()
        return ""

    def note_line(self, children: List[str]) -> str:
        return children[0]

    def keysig(self, children: List[str]) -> List[str]:
        return children

    def auto_color(self, children: List) -> List[str]:
        # children: [guid, int, string, string, string]
        result: List[str] = [f"{{{children[0]}}}", str(children[1])]
        for i in range(2, 5):
            result.append(str(children[i]))
        return result

    def string_in_quotes(self, children: List[str]) -> str:
        return children[0]

    # MIDI event handlers
    def midi_event(self, children: List) -> List[str]:
        """Transform midi_event to list representation

        Uses the midi module to parse MIDI events from Tree/Token children.
        """
        # children: [Tree('midi__PREFIX', 'E'), Token('midi__DELTA', '3840'),
        #            Token('midi__CC_STATUS', 'b0'), Token('midi__HEX_BYTE', '7b'),
        #            Token('midi__HEX_BYTE', '00')]
        # Output: ['E', '3840', 'b0', '7b', '00']
        if children:
            try:
                event = midi.from_children(children)
                return [event.prefix, event.delta, event.status, event.byte2 or event.note or event.controller, event.byte3 or event.velocity or event.value]
            except Exception:
                pass
        return []


# Create transformer instance
_transformer = RPPTransformer()


def loads(string: str) -> Element:
    """Parse RPP content from string using lark parser"""
    parser = _get_parser()
    tree = parser.parse(string)
    # Transform the tree
    return _transformer.transform(tree)


def load(fp: IO[str]) -> Element:
    """Load RPP content from file pointer"""
    return loads(fp.read())


def _tokenize_lark(string: str) -> Tree[Token]:
    """Tokenize RPP content using lark (for debugging)"""
    parser = _get_parser()
    return parser.parse(string)
