from enum import Enum
from typing import Optional

from dataclasses import dataclass


class IdentifierKind(Enum):
    STATIC = "static"
    FIELD = "field"
    ARG = "arg"
    VAR = "var"

    @classmethod
    def fromStr(cls, value: str) -> Optional["IdentifierKind"]:
        try:
            return cls(value)
        except ValueError:
            return None


@dataclass
class SymbolInfo:
    type: str
    kind: IdentifierKind
    i: int


class SymbolTable:
    def __init__(self) -> None:
        self.tbl: dict[str, SymbolInfo] = {}
        self.index: dict[IdentifierKind, int] = {
            IdentifierKind.STATIC: 0,
            IdentifierKind.FIELD: 0,
            IdentifierKind.ARG: 0,
            IdentifierKind.VAR: 0,
        }

    def reset(self) -> None:
        self.tbl.clear()
        self.index = {
            IdentifierKind.STATIC: 0,
            IdentifierKind.FIELD: 0,
            IdentifierKind.ARG: 0,
            IdentifierKind.VAR: 0,
        }

    def define(self, name: str, type: str, kind: IdentifierKind) -> None:
        self.tbl[name] = SymbolInfo(type, kind, self.index[kind])
        self.index[kind] += 1

    def varCount(self, kind: IdentifierKind) -> int:
        return self.index[kind]

    def kindOf(self, name: str) -> IdentifierKind:
        return self.tbl[name].kind

    def typeOf(self, name: str) -> str:
        return self.tbl[name].type

    def indexOf(self, name: str) -> int:
        return self.tbl[name].i

    def hasName(self, name: str) -> bool:
        return name in self.tbl
