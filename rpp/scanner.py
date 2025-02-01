from collections.abc import Iterator
import attr


def tokenize(string: str):
    lex = Lexer()
    lex.input(string)
    return iter(lex)


def lexer():
    return Lexer()


@attr.s
class LexToken:
    type: str = attr.ib()
    value: str = attr.ib()
    lineno: int = attr.ib()


class Lexer:
    _input: str = ""  # 初始化为空字符串
    _iter: Iterator[LexToken] = iter(())  # 初始化为空迭代器

    def input(self, s: str):
        self._input = s
        self._iter = iter(self)

    def token(self):
        return next(self._iter, None)

    def __iter__(self):
        lines = self._input.splitlines()
        for lineno, line in enumerate(lines, start=1):
            is_first_token_in_line = True
            while line:
                line = line.strip()
                if starts_with_quote(line):
                    quote_end = self._find_closing_quote(line, lineno)
                    yield LexToken("STRING", line[1:quote_end], lineno)
                    line = line[quote_end + 1 :]
                else:
                    if is_first_token_in_line:
                        if line.startswith(OPEN):
                            yield LexToken("OPEN", OPEN, lineno)
                            line = line[1:]
                        elif line.startswith(CLOSE):
                            yield LexToken("CLOSE", CLOSE, lineno)
                            line = line[1:]
                        elif starts_with_pipe(line):
                            yield LexToken("STRING", line, lineno)
                            line = ""
                    if line:
                        pair = line.split(maxsplit=1)
                        thing, rest = pair if len(pair) > 1 else (pair[0], "")
                        yield LexToken("STRING", thing, lineno)
                        line = rest
                is_first_token_in_line = False
            yield LexToken("NEWLINE", "\n", lineno)

    def _find_closing_quote(self, line: str, lineno: int):
        try:
            return line.index(line[0], 1)
        except ValueError:
            raise ValueError(f"closing quote not found at line {lineno}")


def starts_with_quote(s: str):
    quotes = "\"'`"
    return s[0] in quotes


def starts_with_pipe(s: str):
    return s[0] == "|"


tokens = (
    "OPEN",
    "CLOSE",
    "STRING",
    "NEWLINE",
)

OPEN = "<"
CLOSE = ">"
