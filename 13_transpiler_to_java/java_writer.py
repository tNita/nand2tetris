"""Emit Java while preserving Jack's word and heap semantics."""

from dataclasses import dataclass
import json
from typing import Optional

from jack_parser import Expression, JackClass, Statement, Subroutine, Token, Variable


JAVA_RESERVED = set("""
    abstract assert boolean break byte case catch char class const continue default
    do double else enum extends final finally float for goto if implements import
    instanceof int interface long native new package private protected public return
    short static strictfp super switch synchronized this throw throws transient try
    void volatile while true false null _ var yield record sealed permits
""".split())


def java_class(name: str) -> str:
    if name in JAVA_RESERVED or name in ("JackRuntime", "java") or name.startswith("J_"):
        return "J_" + name
    return name


@dataclass(frozen=True)
class Signature:
    kind: str
    return_type: str
    arity: int


# The public Jack OS API. User-supplied Jack classes take precedence.
OS_SIGNATURES = {
    "Array": {"new": ("function", "Array", 1), "dispose": ("method", "void", 0)},
    "String": {
        "new": ("constructor", "String", 1), "dispose": ("method", "void", 0),
        "length": ("method", "int", 0), "charAt": ("method", "char", 1),
        "setCharAt": ("method", "void", 2), "appendChar": ("method", "String", 1),
        "eraseLastChar": ("method", "void", 0), "intValue": ("method", "int", 0),
        "setInt": ("method", "void", 1), "newLine": ("function", "char", 0),
        "backSpace": ("function", "char", 0), "doubleQuote": ("function", "char", 0),
    },
    "Math": {name: ("function", "int", arity) for name, arity in (
        ("abs", 1), ("multiply", 2), ("divide", 2),
        ("min", 2), ("max", 2), ("sqrt", 1))},
    "Memory": {"init": ("function", "void", 0), "peek": ("function", "int", 1),
               "poke": ("function", "void", 2), "alloc": ("function", "Array", 1),
               "deAlloc": ("function", "void", 1)},
    "Output": {name: ("function", "void", arity) for name, arity in (
        ("init", 0), ("moveCursor", 2), ("printChar", 1), ("printString", 1),
        ("printInt", 1), ("println", 0), ("backSpace", 0))},
    "Screen": {name: ("function", "void", arity) for name, arity in (
        ("init", 0), ("clearScreen", 0), ("setColor", 1), ("drawPixel", 2),
        ("drawLine", 4), ("drawRectangle", 4), ("drawCircle", 3))},
    "Keyboard": {"init": ("function", "void", 0), "keyPressed": ("function", "char", 0),
                 "readChar": ("function", "char", 0), "readLine": ("function", "String", 1),
                 "readInt": ("function", "int", 1)},
    "Sys": {"init": ("function", "void", 0), "halt": ("function", "void", 0),
            "wait": ("function", "void", 1), "error": ("function", "void", 1)},
}
OS_SIGNATURES["Math"]["init"] = ("function", "void", 0)


class Program:
    def __init__(self, classes: list[JackClass]) -> None:
        self.classes = {}
        self.signatures = {
            name: {method: Signature(*values) for method, values in methods.items()}
            for name, methods in OS_SIGNATURES.items()
        }
        for cls in classes:
            name = cls.name.text
            if name in self.classes:
                raise cls.name.error(f"Duplicate class {name!r}")
            self.classes[name] = cls
            signatures = {}
            for routine in cls.subroutines:
                if routine.name.text in signatures:
                    raise routine.name.error(f"Duplicate subroutine {routine.name.text!r}")
                if routine.kind == "constructor" and routine.return_type != name:
                    raise routine.name.error("A constructor must return its class type")
                signatures[routine.name.text] = Signature(
                    routine.kind, routine.return_type, len(routine.parameters))
            self.signatures[name] = signatures

    def owner(self, name: str) -> str:
        if name in OS_SIGNATURES and name not in self.classes:
            return "JackRuntime." + name
        return java_class(name)

    def routine(self, owner: str, name: str) -> str:
        return self.owner(owner) + ".j_" + name


class JavaWriter:
    def __init__(self, program: Program, cls: JackClass) -> None:
        self.program, self.cls = program, cls
        self.class_variables = {}
        self.field_indices = {}
        self.locals = {}
        self.routine: Optional[Subroutine] = None
        self.lines = []
        self.indent = 0
        for variable in cls.variables:
            name = variable.name.text
            if name in self.class_variables:
                raise variable.name.error(f"Duplicate variable {name!r}")
            self.class_variables[name] = variable
            if variable.kind == "field":
                self.field_indices[name] = len(self.field_indices)

    def emit(self, line: str = "") -> None:
        self.lines.append("    " * self.indent + line if line else "")

    def variable(self, token: Token) -> Variable:
        variable = self.locals.get(token.text) or self.class_variables.get(token.text)
        if variable is None:
            raise token.error(f"Undefined variable {token.text!r}")
        if variable.kind == "field" and self.routine.kind == "function":
            raise token.error("A function cannot access an instance field")
        return variable

    def field_address(self, name: str) -> str:
        return f"j_this + {self.field_indices[name]}"

    def read_variable(self, token: Token) -> str:
        variable = self.variable(token)
        if variable.kind == "field":
            return f"JackRuntime.peek({self.field_address(token.text)})"
        if variable.kind == "static":
            return java_class(self.cls.name.text) + ".j_" + token.text
        return "j_" + token.text

    def call(self, expression: Expression, value_required: bool) -> str:
        target = expression.value
        receiver = None
        owner = self.cls.name.text
        if target is not None:
            if target.text in self.locals or target.text in self.class_variables:
                variable = self.variable(target)
                owner, receiver = variable.type, self.read_variable(target)
                if owner in ("int", "char", "boolean"):
                    raise target.error("A primitive value has no methods")
            else:
                owner = target.text
        methods = self.program.signatures.get(owner)
        signature = methods.get(expression.token.text) if methods is not None else None
        if methods is not None and signature is None:
            raise expression.token.error(f"Unknown subroutine {owner}.{expression.token.text}")
        if signature is not None:
            if signature.kind == "method" and receiver is None:
                if target is None and self.routine.kind != "function":
                    receiver = "j_this"
                else:
                    raise expression.token.error("An instance method requires an object")
            if signature.kind != "method" and receiver is not None:
                raise expression.token.error("Call a function or constructor through its class")
            if len(expression.children) != signature.arity:
                raise expression.token.error(f"Expected {signature.arity} arguments, got {len(expression.children)}")
            if value_required and signature.return_type == "void":
                raise expression.token.error("A void subroutine cannot be used as a value")
        arguments = ([receiver] if receiver is not None else [])
        arguments += [self.expression(argument) for argument in expression.children]
        return self.program.routine(owner, expression.token.text) + "(" + ", ".join(arguments) + ")"

    def expression(self, expression: Expression) -> str:
        kind, value = expression.kind, expression.value
        if kind == "integer":
            return str(value)
        if kind == "string":
            # JSON and Java share these escapes; octal avoids Java's early Unicode
            # translation for control characters other than the named escapes.
            literal = json.dumps(value, ensure_ascii=True)
            for number in range(32):
                literal = literal.replace("\\u%04x" % number, "\\%03o" % number)
            owner = self.program.owner("String")
            return f"JackRuntime.literal({literal}, {owner}::j_new, {owner}::j_appendChar)"
        if kind == "constant":
            if value == "this":
                if self.routine.kind == "function":
                    raise expression.token.error("A function has no 'this' object")
                return "j_this"
            return "-1" if value == "true" else "0"
        if kind == "variable":
            return self.read_variable(expression.token)
        if kind == "index":
            base = self.read_variable(expression.token)
            index = self.expression(expression.children[0])
            return f"JackRuntime.peek((short) ({base} + {index}))"
        if kind == "call":
            return self.call(expression, value_required=True)
        if kind == "unary":
            return f"((short) ({value}({self.expression(expression.children[0])})))"
        left, right = (self.expression(child) for child in expression.children)
        if value in ("*", "/"):
            method = "multiply" if value == "*" else "divide"
            return f"{self.program.routine('Math', method)}({left}, {right})"
        if value in ("<", ">", "="):
            operator = "==" if value == "=" else value
            return f"(({left} {operator} {right}) ? -1 : 0)"
        return f"((short) ({left} {value} {right}))"

    def statements(self, statements: list[Statement]) -> bool:
        returns = False
        for statement in statements:
            # Still validate unreachable Jack code, but omit it for javac.
            before = len(self.lines)
            kind = statement.kind
            guaranteed = False
            if kind == "let":
                variable = self.variable(statement.name)
                value = self.expression(statement.value)
                if statement.index is not None:
                    base = self.read_variable(statement.name)
                    index = self.expression(statement.index)
                    self.emit(f"JackRuntime.poke((short) ({base} + {index}), {value});")
                elif variable.kind == "field":
                    self.emit(f"JackRuntime.poke({self.field_address(statement.name.text)}, {value});")
                else:
                    self.emit(f"{self.read_variable(statement.name)} = {value};")
            elif kind == "do":
                self.emit(self.call(statement.value, value_required=False) + ";")
            elif kind == "return":
                is_void = self.routine.return_type == "void"
                if is_void != (statement.value is None):
                    raise statement.token.error("Return value does not match the subroutine return type")
                value = "0" if is_void else self.expression(statement.value)
                self.emit(f"return {value};")
                guaranteed = True
            else:
                condition = self.expression(statement.value)
                self.emit(f"{kind} (JackRuntime.truth({condition})) {{")
                self.indent += 1
                body_returns = self.statements(statement.body)
                self.indent -= 1
                if kind == "if" and statement.otherwise:
                    self.emit("} else {")
                    self.indent += 1
                    other_returns = self.statements(statement.otherwise)
                    self.indent -= 1
                    guaranteed = body_returns and other_returns
                self.emit("}")
            if returns:
                del self.lines[before:]
            returns = returns or guaranteed
        return returns

    def write_subroutine(self, routine: Subroutine) -> None:
        self.routine, self.locals = routine, {}
        for variable in routine.parameters + routine.locals:
            if variable.name.text in self.locals:
                raise variable.name.error(f"Duplicate variable {variable.name.text!r}")
            self.locals[variable.name.text] = variable
        parameters = ["int j_this"] if routine.kind == "method" else []
        parameters += ["int j_" + parameter.name.text for parameter in routine.parameters]
        self.emit(f"public static int j_{routine.name.text}({', '.join(parameters)}) {{")
        self.indent += 1
        if routine.kind == "constructor":
            alloc = self.program.routine("Memory", "alloc")
            self.emit(f"int j_this = {alloc}({max(1, len(self.field_indices))});")
        for variable in routine.locals:
            self.emit(f"int j_{variable.name.text} = 0;")
        returns = self.statements(routine.body)
        if not returns:
            # A Jack loop may never finish, but Java cannot prove that because
            # its condition is a word rather than a Java constant expression.
            self.emit("throw new java.lang.IllegalStateException(\"Jack subroutine ended without return\");")
        self.indent -= 1
        self.emit("}")
        self.emit()

    def write(self) -> str:
        self.emit("// Generated by jack_transpiler.py. Jack values are signed 16-bit words.")
        self.emit(f"public final class {java_class(self.cls.name.text)} {{")
        self.indent = 1
        for variable in self.cls.variables:
            if variable.kind == "static":
                self.emit(f"private static int j_{variable.name.text} = 0;")
            else:
                self.emit(f"// field {variable.type} {variable.name.text}: this + {self.field_indices[variable.name.text]}")
        self.emit()
        for routine in self.cls.subroutines:
            self.write_subroutine(routine)
        main = self.program.signatures[self.cls.name.text].get("main")
        if main is not None and main.kind == "function" and main.arity == 0:
            self.emit("public static void main(java.lang.String[] args) {")
            self.indent += 1
            self.emit("JackRuntime.run(() -> j_main());")
            self.indent -= 1
            self.emit("}")
        self.indent = 0
        self.emit("}")
        return "\n".join(self.lines) + "\n"
