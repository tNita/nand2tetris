"""Jack lexer, syntax tree, and recursive descent parser."""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Optional


class TranspileError(Exception):
    pass


@dataclass(frozen=True)
class Token:
    text: str
    kind: str
    path: str
    line: int
    column: int

    def error(self, message: str) -> TranspileError:
        return TranspileError(f"{self.path}:{self.line}:{self.column}: {message}")


KEYWORDS = set("""
    class constructor function method field static var int char boolean void
    true false null this let do if else while return
""".split())
LEXEME = re.compile(
    r'(?P<space>\s+)|(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)'
    r'|(?P<string>"[^"\r\n]*")|(?P<integer>[0-9]+)'
    r'|(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)|(?P<symbol>[{}()\[\].,;+*/&|<>=~\-])'
)


def tokenize(source: str, path: str = "<input>") -> list[Token]:
    tokens = []
    offset, line, column = 0, 1, 1
    while offset < len(source):
        if source.startswith("/*", offset) and source.find("*/", offset + 2) < 0:
            raise Token("/*", "comment", path, line, column).error("Unterminated comment")
        match = LEXEME.match(source, offset)
        if match is None:
            message = "Unterminated string" if source[offset] == '"' else "Invalid character"
            raise Token(source[offset], "invalid", path, line, column).error(message)
        text, kind = match.group(), match.lastgroup
        token = Token(text, kind, path, line, column)
        if kind == "integer" and int(text) > 32767:
            raise token.error("Integer constant must be between 0 and 32767")
        if kind == "integer" and match.end() < len(source):
            following = source[match.end()]
            if following.isalpha() or following == "_":
                raise token.error("An identifier cannot start with a digit")
        if kind not in ("space", "comment"):
            if kind == "identifier" and text in KEYWORDS:
                token = Token(text, "keyword", path, line, column)
            tokens.append(token)
        newlines = text.count("\n")
        line += newlines
        column = len(text.rsplit("\n", 1)[-1]) + 1 if newlines else column + len(text)
        offset = match.end()
    tokens.append(Token("<eof>", "eof", path, line, column))
    return tokens


@dataclass
class Variable:
    name: Token
    type: str
    kind: str


@dataclass
class Expression:
    token: Token
    kind: str
    value: Any = None
    children: list["Expression"] = field(default_factory=list)


@dataclass
class Statement:
    token: Token
    kind: str
    value: Optional[Expression] = None
    name: Optional[Token] = None
    index: Optional[Expression] = None
    body: list["Statement"] = field(default_factory=list)
    otherwise: list["Statement"] = field(default_factory=list)


@dataclass
class Subroutine:
    name: Token
    kind: str
    return_type: str
    parameters: list[Variable]
    locals: list[Variable]
    body: list[Statement]


@dataclass
class JackClass:
    name: Token
    variables: list[Variable]
    subroutines: list[Subroutine]


class Parser:
    def __init__(self, source: str, path: str = "<input>") -> None:
        self.tokens = tokenize(source, path)
        self.position = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.position]

    def take(self, text: Optional[str] = None, kind: Optional[str] = None) -> Token:
        token = self.current
        if text is not None and token.text != text:
            raise token.error(f"Expected {text!r}, got {token.text!r}")
        if kind is not None and token.kind != kind:
            raise token.error(f"Expected {kind}, got {token.text!r}")
        self.position += 1
        return token

    def accept(self, text: str) -> bool:
        if self.current.text == text:
            self.take()
            return True
        return False

    def type_name(self, allow_void: bool = False) -> str:
        token = self.current
        if token.text in ("int", "char", "boolean") or (allow_void and token.text == "void"):
            return self.take().text
        return self.take(kind="identifier").text

    def declarations(self, kind: str) -> list[Variable]:
        self.take(kind)
        type_name = self.type_name()
        variables = [Variable(self.take(kind="identifier"), type_name, kind)]
        while self.accept(","):
            variables.append(Variable(self.take(kind="identifier"), type_name, kind))
        self.take(";")
        return variables

    def parse(self) -> JackClass:
        self.take("class")
        name = self.take(kind="identifier")
        self.take("{")
        variables, subroutines = [], []
        while self.current.text in ("static", "field"):
            variables.extend(self.declarations(self.current.text))
        while self.current.text in ("constructor", "function", "method"):
            subroutines.append(self.subroutine())
        self.take("}")
        self.take(kind="eof")
        return JackClass(name, variables, subroutines)

    def subroutine(self) -> Subroutine:
        kind = self.take().text
        return_type = self.type_name(allow_void=True)
        name = self.take(kind="identifier")
        self.take("(")
        parameters = []
        if self.current.text != ")":
            while True:
                type_name = self.type_name()
                parameters.append(Variable(self.take(kind="identifier"), type_name, "argument"))
                if not self.accept(","):
                    break
        self.take(")")
        self.take("{")
        local_variables = []
        while self.current.text == "var":
            local_variables.extend(self.declarations("var"))
        body = self.statements()
        self.take("}")
        return Subroutine(name, kind, return_type, parameters, local_variables, body)

    def block(self) -> list[Statement]:
        self.take("{")
        body = self.statements()
        self.take("}")
        return body

    def statements(self) -> list[Statement]:
        statements = []
        while self.current.text in ("let", "do", "if", "while", "return"):
            token = self.take()
            statement = Statement(token, token.text)
            if token.text == "let":
                statement.name = self.take(kind="identifier")
                if self.accept("["):
                    statement.index = self.expression()
                    self.take("]")
                self.take("=")
                statement.value = self.expression()
                self.take(";")
            elif token.text == "do":
                statement.value = self.call(self.take(kind="identifier"))
                self.take(";")
            elif token.text in ("if", "while"):
                self.take("(")
                statement.value = self.expression()
                self.take(")")
                statement.body = self.block()
                if token.text == "if" and self.accept("else"):
                    statement.otherwise = self.block()
            else:
                if self.current.text != ";":
                    statement.value = self.expression()
                self.take(";")
            statements.append(statement)
        return statements

    def expression(self) -> Expression:
        expression = self.term()
        # Jack gives all binary operators the same precedence.
        while self.current.text in ("+", "-", "*", "/", "&", "|", "<", ">", "="):
            operator = self.take()
            expression = Expression(operator, "binary", operator.text, [expression, self.term()])
        return expression

    def term(self) -> Expression:
        token = self.current
        if token.kind in ("integer", "string"):
            self.take()
            value = int(token.text) if token.kind == "integer" else token.text[1:-1]
            return Expression(token, token.kind, value)
        if token.text in ("true", "false", "null", "this"):
            self.take()
            return Expression(token, "constant", token.text)
        if token.text in ("-", "~"):
            self.take()
            return Expression(token, "unary", token.text, [self.term()])
        if self.accept("("):
            expression = self.expression()
            self.take(")")
            return expression
        if token.kind == "identifier":
            self.take()
            if self.current.text in ("(", "."):
                return self.call(token)
            if self.accept("["):
                index = self.expression()
                self.take("]")
                return Expression(token, "index", token.text, [index])
            return Expression(token, "variable", token.text)
        raise token.error(f"Expected expression, got {token.text!r}")

    def call(self, first: Token) -> Expression:
        target, name = None, first
        if self.accept("."):
            target, name = first, self.take(kind="identifier")
        self.take("(")
        arguments = []
        if self.current.text != ")":
            arguments.append(self.expression())
            while self.accept(","):
                arguments.append(self.expression())
        self.take(")")
        return Expression(name, "call", target, arguments)


def parse_file(path: Path) -> JackClass:
    return Parser(path.read_text(encoding="utf-8"), str(path)).parse()
