from enum import Enum
import re
from typing import Optional, List


class TokenType(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"


class KeyWord(Enum):
    CLASS = "class"
    CONSTRUCTOR = "constructor"
    FUNCTION = "function"
    METHOD = "method"
    FIELD = "field"
    STATIC = "static"
    VAR = "var"
    INT = "int"
    CHAR = "char"
    BOOLEAN = "boolean"
    VOID = "void"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    THIS = "this"
    LET = "let"
    DO = "do"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"

    @classmethod
    def from_lexeme(cls, s: str) -> Optional["KeyWord"]:
        try:
            return cls(s)
        except ValueError:
            return None


JACK_SYMBOLS: List[str] = [
    "{",
    "}",
    "(",
    ")",
    "[",
    "]",
    ".",
    ",",
    ";",
    "+",
    "-",
    "*",
    "/",
    "&",
    "|",
    "<",
    ">",
    "=",
    "~",
]

KEYWORD_PATTERN = (
    r"(?P<KEYWORD>" + "|".join(e.value for e in KeyWord) + r")(?![A-Za-z0-9_])"
)
SYMBOL_PATTERN = r"(?P<SYMBOL>" + "|".join(re.escape(s) for s in JACK_SYMBOLS) + r")"
# 0から32767
INT_CONST_PATTERN = r"(?P<INT_CONST>3276[0-7]|327[0-5]\d|32[0-6]\d{2}|3[0-1]\d{3}|[1-2]\d{4}|[1-9]\d{1,3}|\d)"
STRING_CONST_PATTERN = r'(?P<STRING_CONST>"[^"\n]*")'
IDENTIFIER_PATTERN = r"(?P<IDENTIFIER>[a-zA-Z_][a-zA-Z0-9_]*)"

TOKEN_REGEX = re.compile(
    KEYWORD_PATTERN
    + "|"
    + SYMBOL_PATTERN
    + "|"
    + INT_CONST_PATTERN
    + "|"
    + STRING_CONST_PATTERN
    + "|"
    + IDENTIFIER_PATTERN
)

SKIP_REGEX = re.compile(r"(\s+|//.*|\/\*[\s\S]*?\*\/)")


class JackTokenizer:
    def __init__(self, filepath: str) -> None:
        with open(filepath, "r") as f:
            source_with_comments = f.read()
        self.source = source_with_comments
        self.counter: int = 0
        self.current_token: str = ""

    def hasMoreTokens(self) -> bool:
        next_index = self._skip_ignored_from(self.counter)
        return next_index < len(self.source)

    def advance(self) -> None:
        self.counter = self._skip_ignored_from(self.counter)

        if self.counter >= len(self.source):
            # バグ
            raise Exception("No more tokens")

        token_match = TOKEN_REGEX.match(self.source, self.counter)
        if not token_match:
            raise Exception(f"Unsupported Token: {self.current_token}")
        self.current_token = token_match.group(0)
        self.counter = token_match.end()

    def _skip_ignored_from(self, index: int) -> int:
        length = len(self.source)
        while index < length:
            skip = SKIP_REGEX.match(self.source, index)
            if not skip:
                break
            index = skip.end()
        return index

    def tokenType(self) -> TokenType:
        mtc = TOKEN_REGEX.fullmatch(self.current_token)
        if not mtc:
            # これが発生すればバグ
            raise Exception(f"Unsupported token: f{self.current_token}")

        # 予約語の場合を優先
        if KeyWord.from_lexeme(self.current_token):
            return TokenType.KEYWORD
        return TokenType[mtc.lastgroup]

    def keyWord(self) -> KeyWord:
        if self.tokenType() != TokenType.KEYWORD:
            # これが発生すればバグ
            raise Exception(f"Unsupported token: f{self.current_token}")
        key = KeyWord.from_lexeme(self.current_token)
        if not key:
            raise Exception(f"Unsupported keyword {self.current_token}")
        return key

    def symbol(self) -> str:
        if self.tokenType() != TokenType.SYMBOL:
            # これが発生すればバグ
            raise Exception(f"Unsupported token: f{self.current_token}")
        return self.current_token

    def identifier(self) -> str:
        if self.tokenType() != TokenType.IDENTIFIER:
            # これが発生すればバグ
            raise Exception(f"Unsupported token: f{self.current_token}")
        return self.current_token

    def intVal(self) -> int:
        if self.tokenType() != TokenType.INT_CONST:
            # これが発生すればバグ
            raise Exception(f"Unsupported token: f{self.current_token}")
        return int(self.current_token)

    def stringVal(self) -> str:
        if self.tokenType() != TokenType.STRING_CONST:
            # これが発生すればバグ
            raise Exception(f"Unsupported token: f{self.current_token}")
        return self.current_token[1:-1]
