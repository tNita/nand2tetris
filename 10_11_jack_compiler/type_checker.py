"""Jack type rules and declarations used before compiling subroutine bodies."""

from dataclasses import dataclass
from typing import Iterable

from jack_tokenizer import JackTokenizer


NUMERIC_TYPES = ("int", "char")
PRIMITIVE_TYPES = (*NUMERIC_TYPES, "boolean")
# Array cells are untyped VM words; external classes may be compiled separately.
WORD = "<word>"
UNKNOWN = "<unknown>"


class TypeCheckError(TypeError):
    pass


def is_reference(type_name: str) -> bool:
    return type_name not in (*PRIMITIVE_TYPES, "void", "null", WORD, UNKNOWN)


def is_assignable(expected: str, actual: str) -> bool:
    if "void" in (expected, actual):
        return False
    if expected in (WORD, UNKNOWN) or actual in (WORD, UNKNOWN):
        return True
    if expected == actual or (expected in NUMERIC_TYPES and actual in NUMERIC_TYPES):
        return True
    if actual == "null":
        return is_reference(expected)
    # Jack uses Array for raw memory addresses, including object pointers.
    if "Array" in (expected, actual):
        other = actual if expected == "Array" else expected
        return other in NUMERIC_TYPES or is_reference(other)
    return False


def require_type(expected: str, actual: str, context: str) -> None:
    if not is_assignable(expected, actual):
        raise TypeCheckError(f"{context}: expected {expected}, got {actual}")


def binary_type(op: str, left: str, right: str) -> str:
    context = f"operator '{op}' ({left}, {right})"
    if op == "=":
        if not (is_assignable(left, right) or is_assignable(right, left)):
            raise TypeCheckError(f"{context}: incompatible types")
        return "boolean"
    if op in ("&", "|"):
        if left == "boolean" or right == "boolean":
            require_type("boolean", left, context)
            require_type("boolean", right, context)
            return "boolean"
        if left in (WORD, UNKNOWN) and right in (WORD, UNKNOWN):
            return UNKNOWN if UNKNOWN in (left, right) else WORD
    require_type("int", left, context)
    require_type("int", right, context)
    return "boolean" if op in ("<", ">") else "int"


def unary_type(op: str, operand: str) -> str:
    if op == "~" and operand in ("boolean", WORD, UNKNOWN):
        return operand
    require_type("int", operand, f"operator '{op}'")
    return "int"


@dataclass(frozen=True)
class SubroutineSignature:
    kind: str
    return_type: str
    parameter_types: tuple[str, ...]


# Standard OS interfaces are available even when no OS source is supplied.
OS_SIGNATURES = {
    "Array": {
        "new": ("function", "Array", ("int",)),
        "dispose": ("method", "void", ()),
    },
    "String": {
        "new": ("constructor", "String", ("int",)),
        "dispose": ("method", "void", ()),
        "length": ("method", "int", ()),
        "charAt": ("method", "char", ("int",)),
        "setCharAt": ("method", "void", ("int", "char")),
        "appendChar": ("method", "String", ("char",)),
        "eraseLastChar": ("method", "void", ()),
        "intValue": ("method", "int", ()),
        "setInt": ("method", "void", ("int",)),
        "backSpace": ("function", "char", ()),
        "doubleQuote": ("function", "char", ()),
        "newLine": ("function", "char", ()),
    },
    "Math": {
        "init": ("function", "void", ()),
        "abs": ("function", "int", ("int",)),
        "multiply": ("function", "int", ("int", "int")),
        "divide": ("function", "int", ("int", "int")),
        "min": ("function", "int", ("int", "int")),
        "max": ("function", "int", ("int", "int")),
        "sqrt": ("function", "int", ("int",)),
    },
    "Memory": {
        "init": ("function", "void", ()),
        "peek": ("function", "int", ("int",)),
        "poke": ("function", "void", ("int", "int")),
        "alloc": ("function", "Array", ("int",)),
        "deAlloc": ("function", "void", ("Array",)),
    },
    "Output": {
        "init": ("function", "void", ()),
        "moveCursor": ("function", "void", ("int", "int")),
        "printChar": ("function", "void", ("char",)),
        "printString": ("function", "void", ("String",)),
        "printInt": ("function", "void", ("int",)),
        "println": ("function", "void", ()),
        "backSpace": ("function", "void", ()),
    },
    "Screen": {
        "init": ("function", "void", ()),
        "clearScreen": ("function", "void", ()),
        "setColor": ("function", "void", ("boolean",)),
        "drawPixel": ("function", "void", ("int", "int")),
        "drawLine": ("function", "void", ("int", "int", "int", "int")),
        "drawRectangle": ("function", "void", ("int", "int", "int", "int")),
        "drawCircle": ("function", "void", ("int", "int", "int")),
    },
    "Keyboard": {
        "init": ("function", "void", ()),
        "keyPressed": ("function", "char", ()),
        "readChar": ("function", "char", ()),
        "readLine": ("function", "String", ("String",)),
        "readInt": ("function", "int", ("String",)),
    },
    "Sys": {
        "init": ("function", "void", ()),
        "halt": ("function", "void", ()),
        "error": ("function", "void", ("int",)),
        "wait": ("function", "void", ("int",)),
    },
}


class TypeRegistry:
    def __init__(self) -> None:
        self.classes: dict[str, dict[str, SubroutineSignature]] = {
            name: {method: SubroutineSignature(*sig) for method, sig in methods.items()}
            for name, methods in OS_SIGNATURES.items()
        }
        self.source_classes: set[str] = set()

    def lookup(self, class_name: str, name: str) -> SubroutineSignature:
        if class_name not in self.classes:
            # A separately compiled external class has no available declaration.
            return SubroutineSignature("external", UNKNOWN, ())
        if name not in self.classes[class_name]:
            raise TypeCheckError(f"Unknown subroutine: {class_name}.{name}")
        return self.classes[class_name][name]

    def add_source(self, path: str) -> None:
        tokenizer = JackTokenizer(path)
        tokens = []
        while tokenizer.hasMoreTokens():
            tokenizer.advance()
            tokens.append(tokenizer.current_token)
        position = 0

        def take(expected=None):
            nonlocal position
            if position >= len(tokens):
                raise ValueError(f"{path}: unexpected end of declaration")
            token = tokens[position]
            position += 1
            if expected is not None and token != expected:
                raise ValueError(f"{path}: expected '{expected}', got '{token}'")
            return token

        take("class")
        class_name = take()
        take("{")
        if class_name in self.source_classes:
            raise TypeCheckError(f"{path}: duplicate class: {class_name}")
        self.source_classes.add(class_name)
        signatures = {}
        while position < len(tokens) and tokens[position] != "}":
            kind = take()
            if kind in ("static", "field"):
                while take() != ";":
                    pass
                continue
            if kind not in ("constructor", "function", "method"):
                raise ValueError(f"{path}: invalid subroutine declaration: {kind}")
            return_type, name = take(), take()
            take("(")
            parameters = []
            if position < len(tokens) and tokens[position] != ")":
                while True:
                    parameters.append(take())
                    take()  # Parameter name; the compilation pass validates syntax.
                    if position >= len(tokens) or tokens[position] != ",":
                        break
                    take(",")
            take(")")
            if name in signatures:
                raise TypeCheckError(f"{path}: duplicate subroutine: {class_name}.{name}")
            signatures[name] = SubroutineSignature(kind, return_type, tuple(parameters))
            take("{")
            depth = 1
            while depth:
                token = take()
                if token == "{":
                    depth += 1
                elif token == "}":
                    depth -= 1
        take("}")
        if position != len(tokens):
            raise ValueError(f"{path}: unexpected tokens after class declaration")
        self.classes[class_name] = signatures

    @classmethod
    def from_files(cls, paths: Iterable[str]) -> "TypeRegistry":
        registry = cls()
        for path in paths:
            registry.add_source(path)
        return registry
