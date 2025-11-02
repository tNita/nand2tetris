from __future__ import annotations

from enum import Enum
from symbol import IdentifierKind


class Segment(Enum):
    CONSTANT = "constant"
    ARGUMENT = "argument"
    LOCAL = "local"
    STATIC = "static"
    THIS = "this"
    THAT = "that"
    POINTER = "pointer"
    TEMP = "temp"

    @classmethod
    def fromIdentifierKind(cls, kind: IdentifierKind) -> Segment:
        mapping = {
            IdentifierKind.STATIC: cls.STATIC,
            IdentifierKind.FIELD: cls.THIS,
            IdentifierKind.ARG: cls.ARGUMENT,
            IdentifierKind.VAR: cls.LOCAL,
        }
        return mapping[kind]


class ArithmeticCommand(Enum):
    ADD = "add"
    SUB = "sub"
    NEG = "neg"
    EQ = "eq"
    GT = "gt"
    LT = "lt"
    AND = "and"
    OR = "or"
    NOT = "not"


class VMWriter:
    def __init__(self, fileName: str) -> None:
        # VMコードを書き込む出力ファイルをオープン
        self.fileName = fileName
        self._file = open(fileName, "w", encoding="utf-8", newline="")

    def _writeLine(self, line: str) -> None:
        # Jackコンパイラの仕様に合わせてLFで改行する
        self._file.write(f"{line}\n")

    def writePush(self, segment: Segment, index: int) -> None:
        self._writeLine(f"push {segment.value} {index}")

    def writePop(self, segment: Segment, index: int) -> None:
        self._writeLine(f"pop {segment.value} {index}")

    def writeArithmetic(self, command: ArithmeticCommand | str) -> None:
        cmd = command.value if isinstance(command, ArithmeticCommand) else str(command)
        self._writeLine(cmd)

    def writeLabel(self, label: str) -> None:
        self._writeLine(f"label {label}")

    def writeGoto(self, label: str) -> None:
        self._writeLine(f"goto {label}")

    def writeIf(self, label: str) -> None:
        self._writeLine(f"if-goto {label}")

    def writeCall(self, name: str, nArgs: int) -> None:
        self._writeLine(f"call {name} {nArgs}")

    def writeFunction(self, name: str, nLocals: int) -> None:
        self._writeLine(f"function {name} {nLocals}")

    def writeReturn(self) -> None:
        self._writeLine("return")

    def close(self) -> None:
        self._file.close()
