from enum import Enum
from typing import Optional

from jack_tokenizer import JackTokenizer, TokenType, KeyWord, Symbol
from symbol import IdentifierKind, SymbolTable
from xml.etree.ElementTree import Element
from vm_writer import ArithmeticCommand, VMWriter, Segment
from char_code import CHAR_TO_CODE
from type_checker import (
    TypeCheckError,
    TypeRegistry,
    WORD,
    binary_type,
    is_reference,
    require_type,
    unary_type,
)


import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s: %(message)s"
)


PRIMITIVE_TYPE = (KeyWord.INT.value, KeyWord.CHAR.value, KeyWord.BOOLEAN.value)

ARITHMETIC_OP_MAP = {
    Symbol.PLUS.value: ArithmeticCommand.ADD,
    Symbol.MINUS.value: ArithmeticCommand.SUB,
    Symbol.AMPERSAND.value: ArithmeticCommand.AND,
    Symbol.PIPE.value: ArithmeticCommand.OR,
    Symbol.LT.value: ArithmeticCommand.LT,
    Symbol.GT.value: ArithmeticCommand.GT,
    Symbol.EQ.value: ArithmeticCommand.EQ,
}

OS_OP_MAP = {
    Symbol.ASTERISK.value: "Math.multiply",
    Symbol.SLASH.value: "Math.divide",
}

UNARY_OP = (Symbol.MINUS.value, Symbol.TILDE.value)

KEYWORD_CONSTANT = (
    KeyWord.TRUE.value,
    KeyWord.FALSE.value,
    KeyWord.NULL.value,
    KeyWord.THIS.value,
)

KEYWORD_SUBROUTINE = (
    KeyWord.CONSTRUCTOR.value,
    KeyWord.FUNCTION.value,
    KeyWord.METHOD.value,
)

KEYWORD_CLASSVARDEC = (KeyWord.STATIC.value, KeyWord.FIELD.value)


class ElementTag(Enum):
    CLASS = "class"
    CLASS_VAR_DEC = "classVarDec"
    SUBROUTINE_DEC = "subroutineDec"
    PARAMETER_LIST = "parameterList"
    SUBROUTINE_BODY = "subroutineBody"
    VAR_DEC = "varDec"
    STATEMENTS = "statements"
    LET_STATEMENT = "letStatement"
    IF_STATEMENT = "ifStatement"
    WHILE_STATEMENT = "whileStatement"
    DO_STATEMENT = "doStatement"
    RETURN_STATEMENT = "returnStatement"
    EXPRESSION = "expression"
    EXPRESSION_LIST = "expressionList"
    TERM = "term"


class Usage(Enum):
    DEFINED = "defined"
    USED = "used"


class SymbolCategory(Enum):
    FIELD = "field"
    STATIC = "static"
    VAR = "var"
    ARGUMENT = "argument"
    CLASS = "class"
    SUBROUTINE = "subroutine"

    @classmethod
    def fromIdentifierKind(cls, kind: IdentifierKind) -> "SymbolCategory":
        mapping = {
            IdentifierKind.STATIC: cls.STATIC,
            IdentifierKind.FIELD: cls.FIELD,
            IdentifierKind.ARG: cls.ARGUMENT,
            IdentifierKind.VAR: cls.VAR,
        }
        return mapping[kind]


LABEL_BASE = "L{0}"


class CompilationEngine:
    def __init__(
        self,
        tokenizer: JackTokenizer,
        fileName: str,
        typeRegistry: Optional[TypeRegistry] = None,
    ) -> None:
        self.tokenizer = tokenizer
        self.typeRegistry = (
            typeRegistry
            if typeRegistry is not None
            else TypeRegistry.from_files([tokenizer.filepath])
        )
        self.classTable = SymbolTable()
        self.subroutineTable = SymbolTable()
        self.currentClassName: Optional[str] = None
        self.currentSubroutineName = ""
        self.currentSubroutineKind: Optional[KeyWord] = None
        self.currentReturnType = "void"
        self.labelNum = 0
        self.vmWriter = VMWriter(fileName)

        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        else:
            raise Exception("this file is empty")

    def compileClass(self) -> None:
        try:
            self._compileClass()
        except TypeCheckError as error:
            start = self.tokenizer.token_start
            line = self.tokenizer.source.count("\n", 0, start) + 1
            column = start - self.tokenizer.source.rfind("\n", 0, start)
            name = f"{self.currentClassName}.{self.currentSubroutineName}"
            raise TypeCheckError(
                f"{self.tokenizer.filepath}:{line}:{column}: {name}: {error}"
            ) from None

    def _compileClass(self) -> None:

        self._eatSpecified(KeyWord.CLASS.value)
        if self.tokenizer.tokenType() != TokenType.IDENTIFIER:
            raise Exception(f"Invalid class name: {self._currentTokenValue()}")
        self.currentClassName = self._currentTokenValue()
        self._eatCurrentToken()
        self._eatSpecified(Symbol.LBRACE.value)

        while self._currentTokenValue() in KEYWORD_CLASSVARDEC:
            self.compileClassVarDec()

        while self._currentTokenValue() in KEYWORD_SUBROUTINE:
            self.compileSubroutine()

        self._eatSpecified(Symbol.RBRACE.value)

    def compileClassVarDec(self) -> None:
        if self._currentTokenValue() not in KEYWORD_CLASSVARDEC:
            raise Exception(f"Invalid syntax: {self._currentTokenValue()}")

        kindStr = self._currentTokenValue()
        if kindStr not in (IdentifierKind.STATIC.value, IdentifierKind.FIELD.value):
            raise Exception(f"Unsupported class variable kind: {kindStr}")
        kind = (
            IdentifierKind.STATIC
            if kindStr == IdentifierKind.STATIC.value
            else IdentifierKind.FIELD
        )
        segment = Segment.STATIC if kind == IdentifierKind.STATIC else Segment.THIS

        self._eatCurrentToken()
        typeStr = self._currentTokenValue()
        self._compileType()
        name = self._currentTokenValue()
        self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
        self._defineSymbol(self.classTable, name, typeStr, kind)

        self.vmWriter.writePush(segment, self.classTable.indexOf(name))

        while self._currentTokenValue() == Symbol.COMMA.value:
            self._eatSpecified(Symbol.COMMA.value)
            name = self._currentTokenValue()
            self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
            self._defineSymbol(self.classTable, name, typeStr, kind)
            self.vmWriter.writePush(segment, self.classTable.indexOf(name))

        self._eatSpecified(Symbol.SEMICOLON.value)

    def compileSubroutine(self) -> None:
        if self._currentTokenValue() not in KEYWORD_SUBROUTINE:
            raise Exception(f"Invalid syntax: {self._currentTokenValue()}")

        subroutineKind = self.tokenizer.keyWord()
        self.currentSubroutineKind = subroutineKind
        self._eatCurrentToken()

        self.currentReturnType = self._currentTokenValue()
        if self._currentTokenValue() == KeyWord.VOID.value:
            self._eatCurrentToken()
        else:
            self._compileType()

        if self.tokenizer.tokenType() != TokenType.IDENTIFIER:
            raise Exception(f"Invalid subroutine name: {self._currentTokenValue()}")
        subroutineName = self._currentTokenValue()
        self.currentSubroutineName = subroutineName
        if subroutineKind == KeyWord.CONSTRUCTOR:
            if self.currentReturnType != self.currentClassName:
                raise TypeCheckError(
                    f"constructor must return {self.currentClassName}, "
                    f"got {self.currentReturnType}"
                )
        self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
        self._eatSpecified(Symbol.LPAREN.value)

        self.subroutineTable = SymbolTable()
        if subroutineKind == KeyWord.METHOD:
            if not self.currentClassName:
                raise Exception("Class name must be set before compiling methods")
            self._defineSymbol(
                self.subroutineTable, "this", self.currentClassName, IdentifierKind.ARG
            )

        self.compileParameterList()
        self._eatSpecified(Symbol.RPAREN.value)

        # サブルーチン本体をコンパイル
        self._eatSpecified(Symbol.LBRACE.value)

        while self._currentTokenValue() == KeyWord.VAR.value:
            self.compileVarDec()

        self.vmWriter.writeFunction(
            f"{self.currentClassName}.{subroutineName}",
            self.subroutineTable.varCount(IdentifierKind.VAR),
        )

        if subroutineKind == KeyWord.METHOD:
            self.vmWriter.writePush(Segment.ARGUMENT, 0)
            self.vmWriter.writePop(Segment.POINTER, 0)

        if subroutineKind == KeyWord.CONSTRUCTOR:
            self.vmWriter.writePush(
                Segment.CONSTANT, self.classTable.varCount(IdentifierKind.FIELD)
            )
            self.vmWriter.writeCall("Memory.alloc", 1)
            self.vmWriter.writePop(Segment.POINTER, 0)

        self.compileStatements()

        self._eatSpecified(Symbol.RBRACE.value)

    def compileParameterList(self) -> int:
        cnt = 0
        if self._currentTokenValue() == Symbol.RPAREN.value:
            return cnt

        while True:
            cnt += 1
            typeStr = self._currentTokenValue()
            self._compileType()
            if self.tokenizer.tokenType() != TokenType.IDENTIFIER:
                raise Exception(f"Invalid parameter name: {self._currentTokenValue()}")
            name = self._currentTokenValue()
            self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
            self._defineSymbol(self.subroutineTable, name, typeStr, IdentifierKind.ARG)

            if self._currentTokenValue() != Symbol.COMMA.value:
                break

            self._eatSpecified(Symbol.COMMA.value)
        return cnt

    def compileVarDec(self) -> None:
        self._eatSpecified(KeyWord.VAR.value)
        typeStr = self._currentTokenValue()
        self._compileType()

        name = self._currentTokenValue()
        self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
        self._defineSymbol(self.subroutineTable, name, typeStr, IdentifierKind.VAR)

        while self._currentTokenValue() == Symbol.COMMA.value:
            self._eatSpecified(Symbol.COMMA.value)
            if self.tokenizer.tokenType() != TokenType.IDENTIFIER:
                raise Exception(f"Invalid variable name: {self._currentTokenValue()}")
            name = self._currentTokenValue()
            self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
            self._defineSymbol(self.subroutineTable, name, typeStr, IdentifierKind.VAR)

        self._eatSpecified(Symbol.SEMICOLON.value)

    def compileStatements(self) -> None:
        while self._currentTokenValue() in (
            KeyWord.LET.value,
            KeyWord.IF.value,
            KeyWord.WHILE.value,
            KeyWord.DO.value,
            KeyWord.RETURN.value,
        ):
            if self._currentTokenValue() == KeyWord.LET.value:
                self.compileLet()
            elif self._currentTokenValue() == KeyWord.IF.value:
                self.compileIf()
            elif self._currentTokenValue() == KeyWord.WHILE.value:
                self.compileWhile()
            elif self._currentTokenValue() == KeyWord.DO.value:
                self.compileDo()
            else:
                self.compileReturn()

    def compileLet(self) -> None:
        self._eatSpecified(KeyWord.LET.value)

        name = self._currentTokenValue()
        segment, index, targetType = self._findSymbol(name)
        self._eatSpecifiedTokenType(TokenType.IDENTIFIER)

        isArr = self._currentTokenValue() == Symbol.LBRACKET.value

        if isArr:
            self._requireArray(targetType)
            self._eatSpecified(Symbol.LBRACKET.value)
            self.vmWriter.writePush(segment, index)
            require_type("int", self.compileExpression(), "array index")
            self.vmWriter.writeArithmetic(ArithmeticCommand.ADD)
            self._eatSpecified(Symbol.RBRACKET.value)

        self._eatSpecified(Symbol.EQ.value)
        valueType = self.compileExpression()
        require_type(WORD if isArr else targetType, valueType, f"assignment to {name}")

        if isArr:
            self.vmWriter.writePop(Segment.TEMP, 0)
            self.vmWriter.writePop(Segment.POINTER, 1)
            self.vmWriter.writePush(Segment.TEMP, 0)
            self.vmWriter.writePop(Segment.THAT, 0)
        else:
            self.vmWriter.writePop(segment, index)

        self._eatSpecified(Symbol.SEMICOLON.value)

    def compileIf(self) -> None:
        self._eatSpecified(KeyWord.IF.value)
        self._eatSpecified(Symbol.LPAREN.value)
        require_type("boolean", self.compileExpression(), "if condition")
        self._eatSpecified(Symbol.RPAREN.value)
        self._eatSpecified(Symbol.LBRACE.value)
        self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)
        labelIf = self._createLabel()
        self.vmWriter.writeIf(labelIf)

        self.compileStatements()
        self._eatSpecified(Symbol.RBRACE.value)

        if self._currentTokenValue() != KeyWord.ELSE.value:
            self.vmWriter.writeLabel(labelIf)
            return

        labelElse = self._createLabel()
        self.vmWriter.writeGoto(labelElse)
        self.vmWriter.writeLabel(labelIf)

        self._eatSpecified(KeyWord.ELSE.value)
        self._eatSpecified(Symbol.LBRACE.value)
        self.compileStatements()
        self._eatSpecified(Symbol.RBRACE.value)
        self.vmWriter.writeLabel(labelElse)

    def compileWhile(self) -> None:
        self._eatSpecified(KeyWord.WHILE.value)
        self._eatSpecified(Symbol.LPAREN.value)

        labelStart = self._createLabel()
        self.vmWriter.writeLabel(labelStart)

        require_type("boolean", self.compileExpression(), "while condition")
        self._eatSpecified(Symbol.RPAREN.value)
        self._eatSpecified(Symbol.LBRACE.value)

        self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)

        labelEnd = self._createLabel()
        self.vmWriter.writeIf(labelEnd)
        self.compileStatements()
        self.vmWriter.writeGoto(labelStart)

        self._eatSpecified(Symbol.RBRACE.value)
        self.vmWriter.writeLabel(labelEnd)

    def compileDo(self) -> None:
        self._eatSpecified(KeyWord.DO.value)

        name = self._currentTokenValue()
        self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
        self._compileCall(name)

        self.vmWriter.writePop(Segment.TEMP, 0)

        self._eatSpecified(Symbol.SEMICOLON.value)

    def compileReturn(self) -> None:
        self._eatSpecified(KeyWord.RETURN.value)

        if self._currentTokenValue() == Symbol.SEMICOLON.value:
            if self.currentReturnType != "void":
                raise TypeCheckError(f"return: expected {self.currentReturnType}, got void")
        else:
            valueType = self.compileExpression()
            require_type(self.currentReturnType, valueType, "return")

        self._eatSpecified(Symbol.SEMICOLON.value)
        self.vmWriter.writeReturn()

    def compileExpression(self) -> str:
        resultType = self.compileTerm()
        while (
            self._currentTokenValue() in ARITHMETIC_OP_MAP
            or self._currentTokenValue() in OS_OP_MAP
        ):
            op = self._currentTokenValue()
            self._eatCurrentToken()
            resultType = binary_type(op, resultType, self.compileTerm())
            if op in ARITHMETIC_OP_MAP:
                self.vmWriter.writeArithmetic(ARITHMETIC_OP_MAP[op])
            else:
                self.vmWriter.writeCall(OS_OP_MAP[op], 2)
        return resultType

    def compileExpressionList(self) -> list[str]:
        types = []
        if self._currentTokenValue() == Symbol.RPAREN.value:
            return types

        types.append(self.compileExpression())

        while self._currentTokenValue() == Symbol.COMMA.value:
            self._eatSpecified(Symbol.COMMA.value)
            types.append(self.compileExpression())

        return types

    def compileTerm(self) -> str:
        tokenType = self.tokenizer.tokenType()

        if tokenType == TokenType.INT_CONST:
            self.vmWriter.writePush(Segment.CONSTANT, self.tokenizer.intVal())
            self._eatCurrentToken()
            return "int"

        if tokenType == TokenType.STRING_CONST:
            stringVal = self.tokenizer.stringVal()
            self.vmWriter.writePush(Segment.CONSTANT, len(stringVal))
            self.vmWriter.writeCall("String.new", 1)
            self.vmWriter.writePop(Segment.TEMP, 0)
            for c in stringVal:
                self.vmWriter.writePush(Segment.TEMP, 0)
                self.vmWriter.writePush(Segment.CONSTANT, CHAR_TO_CODE[c])
                self.vmWriter.writeCall("String.appendChar", 2)
                self.vmWriter.writePop(Segment.TEMP, 0)
            self.vmWriter.writePush(Segment.TEMP, 0)
            self._eatCurrentToken()
            return "String"

        if self._currentTokenValue() in KEYWORD_CONSTANT:
            keyword = self._currentTokenValue()
            self._eatCurrentToken()
            if keyword == KeyWord.TRUE.value:
                self.vmWriter.writePush(Segment.CONSTANT, 0)
                self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)
            elif keyword in (KeyWord.FALSE.value, KeyWord.NULL.value):
                self.vmWriter.writePush(Segment.CONSTANT, 0)
            elif keyword == KeyWord.THIS.value:
                if self.currentSubroutineKind == KeyWord.FUNCTION:
                    raise TypeCheckError("this is not available in a function")
                self.vmWriter.writePush(Segment.POINTER, 0)
            if keyword == KeyWord.THIS.value:
                return self.currentClassName
            return "null" if keyword == KeyWord.NULL.value else "boolean"

        if self._currentTokenValue() == Symbol.LPAREN.value:
            self._eatSpecified(Symbol.LPAREN.value)
            resultType = self.compileExpression()
            self._eatSpecified(Symbol.RPAREN.value)
            return resultType

        if self._currentTokenValue() in (Symbol.MINUS.value, Symbol.TILDE.value):
            op = self._currentTokenValue()
            self._eatCurrentToken()
            resultType = unary_type(op, self.compileTerm())
            if op == Symbol.MINUS.value:
                self.vmWriter.writeArithmetic(ArithmeticCommand.NEG)
            else:
                self.vmWriter.writeArithmetic(ArithmeticCommand.NOT)
            return resultType

        if tokenType != TokenType.IDENTIFIER:
            raise Exception(f"Invalid syntax {self._currentTokenValue()}")

        # 先読みが必要なもの
        prevToken = self._currentTokenValue()
        self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
        if self._currentTokenValue() == Symbol.LBRACKET.value:
            self._eatSpecified(Symbol.LBRACKET.value)
            seg, index, typeName = self._findSymbol(prevToken)
            self._requireArray(typeName)
            self.vmWriter.writePush(seg, index)
            require_type("int", self.compileExpression(), "array index")
            self.vmWriter.writeArithmetic(ArithmeticCommand.ADD)
            self.vmWriter.writePop(Segment.POINTER, 1)
            self.vmWriter.writePush(Segment.THAT, 0)
            self._eatSpecified(Symbol.RBRACKET.value)
            return WORD
        elif self._currentTokenValue() in (Symbol.LPAREN.value, Symbol.DOT.value):
            resultType = self._compileCall(prevToken)
            if resultType == "void":
                raise TypeCheckError("void subroutine cannot be used in an expression")
            return resultType
        else:
            # 変数のみ
            seg, index, typeName = self._findSymbol(prevToken)
            self.vmWriter.writePush(seg, index)
            return typeName

    def _compileCall(self, name: str) -> str:
        argOffset = 0
        if self._currentTokenValue() == Symbol.DOT.value:
            self._eatSpecified(Symbol.DOT.value)
            methodName = self._currentTokenValue()
            self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
            className = name
            isInstance = self._hasSymbol(name)
            if isInstance:
                seg, index, className = self._findSymbol(name)
                if not is_reference(className):
                    raise TypeCheckError(f"cannot call a method on {className}")
                self.vmWriter.writePush(seg, index)
                argOffset = 1
            signature = self.typeRegistry.lookup(className, methodName)
            if signature.kind != "external":
                if (signature.kind == "method") != isInstance:
                    message = (
                        "method requires an instance"
                        if signature.kind == "method"
                        else "function/constructor requires a class receiver"
                    )
                    raise TypeCheckError(
                        f"{className}.{methodName}: {message}"
                    )
        else:
            className, methodName = self.currentClassName, name
            signature = self.typeRegistry.lookup(className, methodName)
            if signature.kind == "method":
                if self.currentSubroutineKind == KeyWord.FUNCTION:
                    raise TypeCheckError(f"{className}.{methodName}: method requires an instance")
                self.vmWriter.writePush(Segment.POINTER, 0)
                argOffset = 1

        self._eatSpecified(Symbol.LPAREN.value)
        argumentTypes = self.compileExpressionList()
        qualifiedName = f"{className}.{methodName}"
        if signature.kind != "external":
            if len(argumentTypes) != len(signature.parameter_types):
                raise TypeCheckError(
                    f"{qualifiedName}: expected {len(signature.parameter_types)} arguments, "
                    f"got {len(argumentTypes)}"
                )
            for i, (expected, actual) in enumerate(
                zip(signature.parameter_types, argumentTypes), start=1
            ):
                require_type(expected, actual, f"{qualifiedName} argument {i}")
        self.vmWriter.writeCall(qualifiedName, len(argumentTypes) + argOffset)
        self._eatSpecified(Symbol.RPAREN.value)
        return signature.return_type

    def _requireArray(self, typeName: str) -> None:
        if typeName != "Array":
            raise TypeCheckError(f"array access: expected Array, got {typeName}")

    def _compileType(self) -> None:
        if (
            self.tokenizer.tokenType() == TokenType.KEYWORD
            and self._currentTokenValue() in PRIMITIVE_TYPE
        ):
            self._eatCurrentToken()
            return

        if self.tokenizer.tokenType() == TokenType.IDENTIFIER:
            self._eatSpecifiedTokenType(TokenType.IDENTIFIER)
            return

        raise Exception(f"Invalid syntax: {self._currentTokenValue()}")

    def _eatSpecifiedTokenType(self, tokenType: TokenType) -> None:
        if self.tokenizer.tokenType() != tokenType:
            raise Exception(f"Invalid syntax: {self._currentTokenValue()}")

        self._eatCurrentToken()

    def _eatCurrentToken(self) -> None:
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def _eatSpecified(self, token: str) -> None:
        if self._currentTokenValue() != token:
            raise Exception(f"Invalid syntax: {self._currentTokenValue()}")

        self._eatCurrentToken()

    def _createLabel(self) -> str:
        label = LABEL_BASE.format(self.labelNum)
        self.labelNum += 1
        return label

    def _defineSymbol(
        self, table: SymbolTable, name: str, type_name: str, kind: IdentifierKind
    ) -> int:
        if table.hasName(name):
            raise TypeCheckError(f"duplicate variable: {name}")
        table.define(name, type_name, kind)
        return table.indexOf(name)

    def _hasSymbol(self, name: str) -> bool:
        return self.subroutineTable.hasName(name) or self.classTable.hasName(name)

    def _findSymbol(self, name: str) -> tuple[Segment, int, str]:
        if self.subroutineTable.hasName(name):
            kind = self.subroutineTable.kindOf(name)
            segment = Segment.fromIdentifierKind(kind)
            return (
                segment,
                self.subroutineTable.indexOf(name),
                self.subroutineTable.typeOf(name),
            )
        if self.classTable.hasName(name):
            kind = self.classTable.kindOf(name)
            if kind == IdentifierKind.FIELD and self.currentSubroutineKind == KeyWord.FUNCTION:
                raise TypeCheckError(f"field {name} is not available in a function")
            segment = Segment.fromIdentifierKind(kind)
            return segment, self.classTable.indexOf(name), self.classTable.typeOf(name)
        raise TypeCheckError(f"{name} is not found in symbol table")

    def _currentTokenValue(self) -> str:
        token_type = self.tokenizer.tokenType()
        if token_type == TokenType.STRING_CONST:
            return self.tokenizer.stringVal()
        if token_type == TokenType.INT_CONST:
            return str(self.tokenizer.intVal())
        if token_type == TokenType.IDENTIFIER:
            return self.tokenizer.identifier()
        if token_type == TokenType.KEYWORD:
            return self.tokenizer.keyWord().value
        if token_type == TokenType.SYMBOL:
            return self.tokenizer.symbol()
        raise Exception(f"Unsupported token type: {token_type}")
