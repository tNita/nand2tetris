from enum import Enum

from jack_tokenizer import JackTokenizer, TokenType, KeyWord, Symbol
from xml.etree.ElementTree import Element
PRIMITIVE_TYPE = (KeyWord.INT.value, KeyWord.CHAR.value, KeyWord.BOOLEAN.value)

KEYWORD_SUBROUTINE = (
    KeyWord.CONSTRUCTOR.value,
    KeyWord.FUNCTION.value,
    KeyWord.METHOD.value,
)

KEYWORD_CLASSVARDEC = (KeyWord.STATIC.value, KeyWord.FIELD.value)

OP = (
    Symbol.PLUS.value,
    Symbol.MINUS.value,
    Symbol.ASTERISK.value,
    Symbol.SLASH.value,
    Symbol.AMPERSAND.value,
    Symbol.PIPE.value,
    Symbol.LT.value,
    Symbol.GT.value,
    Symbol.EQ.value,
)
UNARY_OP = (Symbol.MINUS.value, Symbol.TILDE.value)

KEYWORD_CONSTANT = (
    KeyWord.TRUE.value,
    KeyWord.FALSE.value,
    KeyWord.NULL.value,
    KeyWord.THIS.value,
)


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


class CompilationEngine:
    def __init__(self, tokenizer: JackTokenizer) -> None:
        self.tokenizer = tokenizer
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        else:
            raise Exception(f"this file is empty")

    def compileClass(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.CLASS)

        ele.append(self._createSpecifiedElement(KeyWord.CLASS.value))
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))
        ele.append(self._createSpecifiedElement(Symbol.LBRACE.value))

        while self.tokenizer.current_token in KEYWORD_CLASSVARDEC:
            ele.append(self.compileClassVarDec())

        while self.tokenizer.current_token in KEYWORD_SUBROUTINE:
            ele.append(self.compileSubroutine())

        ele.append(self._createSpecifiedElement(Symbol.RBRACE.value))
        return ele

    def compileClassVarDec(self) -> Element:
        if self.tokenizer.current_token not in KEYWORD_CLASSVARDEC:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createNonTerminalElement(ElementTag.CLASS_VAR_DEC)
        ele.append(self._createCurrentTokenElement())
        ele.append(self._compileType())
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        while self.tokenizer.current_token == Symbol.COMMA.value:
            ele.append(self._createSpecifiedElement(Symbol.COMMA.value))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement(Symbol.SEMICOLON.value))
        return ele

    def compileSubroutine(self) -> Element:
        if self.tokenizer.current_token not in KEYWORD_SUBROUTINE:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createNonTerminalElement(ElementTag.SUBROUTINE_DEC)
        ele.append(self._createCurrentTokenElement())
        if self.tokenizer.current_token == KeyWord.VOID.value:
            ele.append(self._createCurrentTokenElement())
        else:
            ele.append(self._compileType())
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))
        ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))

        ele.append(self.compileParameterList())
        ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
        ele.append(self.compileSubroutineBody())
        return ele

    def compileParameterList(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.PARAMETER_LIST)

        if self.tokenizer.current_token == Symbol.RPAREN.value:
            return ele

        while True:
            ele.append(self._compileType())
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

            if self.tokenizer.current_token != Symbol.COMMA.value:
                break

            ele.append(self._createSpecifiedElement(Symbol.COMMA.value))

        return ele

    def compileSubroutineBody(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.SUBROUTINE_BODY)
        ele.append(self._createSpecifiedElement(Symbol.LBRACE.value))

        while self.tokenizer.current_token == KeyWord.VAR.value:
            ele.append(self.compileVarDec())

        ele.append(self.compileStatements())
        ele.append(self._createSpecifiedElement(Symbol.RBRACE.value))
        return ele

    def compileVarDec(self) -> Element:
        if self.tokenizer.current_token != KeyWord.VAR.value:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createNonTerminalElement(ElementTag.VAR_DEC)
        ele.append(self._createSpecifiedElement(KeyWord.VAR.value))
        ele.append(self._compileType())
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        while self.tokenizer.current_token == Symbol.COMMA.value:
            ele.append(self._createSpecifiedElement(Symbol.COMMA.value))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement(Symbol.SEMICOLON.value))
        return ele

    def compileStatements(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.STATEMENTS)

        while self.tokenizer.current_token in (
            KeyWord.LET.value,
            KeyWord.IF.value,
            KeyWord.WHILE.value,
            KeyWord.DO.value,
            KeyWord.RETURN.value,
        ):
            if self.tokenizer.current_token == KeyWord.LET.value:
                ele.append(self.compileLet())
            elif self.tokenizer.current_token == KeyWord.IF.value:
                ele.append(self.compileIf())
            elif self.tokenizer.current_token == KeyWord.WHILE.value:
                ele.append(self.compileWhile())
            elif self.tokenizer.current_token == KeyWord.DO.value:
                ele.append(self.compileDo())
            else:
                ele.append(self.compileReturn())

        return ele

    def compileLet(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.LET_STATEMENT)
        ele.append(self._createSpecifiedElement(KeyWord.LET.value))
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        if self.tokenizer.current_token == Symbol.LBRACKET.value:
            ele.append(self._createSpecifiedElement(Symbol.LBRACKET.value))
            ele.append(self.compileExpression())
            ele.append(self._createSpecifiedElement(Symbol.RBRACKET.value))

        ele.append(self._createSpecifiedElement(Symbol.EQ.value))
        ele.append(self.compileExpression())
        ele.append(self._createSpecifiedElement(Symbol.SEMICOLON.value))
        return ele

    def compileIf(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.IF_STATEMENT)
        ele.append(self._createSpecifiedElement(KeyWord.IF.value))
        ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))
        ele.append(self.compileExpression())
        ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
        ele.append(self._createSpecifiedElement(Symbol.LBRACE.value))
        ele.append(self.compileStatements())
        ele.append(self._createSpecifiedElement(Symbol.RBRACE.value))

        if self.tokenizer.current_token == KeyWord.ELSE.value:
            ele.append(self._createSpecifiedElement(KeyWord.ELSE.value))
            ele.append(self._createSpecifiedElement(Symbol.LBRACE.value))
            ele.append(self.compileStatements())
            ele.append(self._createSpecifiedElement(Symbol.RBRACE.value))

        return ele

    def compileWhile(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.WHILE_STATEMENT)
        ele.append(self._createSpecifiedElement(KeyWord.WHILE.value))
        ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))
        ele.append(self.compileExpression())
        ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
        ele.append(self._createSpecifiedElement(Symbol.LBRACE.value))
        ele.append(self.compileStatements())
        ele.append(self._createSpecifiedElement(Symbol.RBRACE.value))
        return ele

    def compileDo(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.DO_STATEMENT)
        ele.append(self._createSpecifiedElement(KeyWord.DO.value))
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        if self.tokenizer.current_token == Symbol.DOT.value:
            ele.append(self._createSpecifiedElement(Symbol.DOT.value))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))
        ele.append(self.compileExpressionList())
        ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
        ele.append(self._createSpecifiedElement(Symbol.SEMICOLON.value))
        return ele

    def compileReturn(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.RETURN_STATEMENT)
        ele.append(self._createSpecifiedElement(KeyWord.RETURN.value))

        if self.tokenizer.current_token != Symbol.SEMICOLON.value:
            ele.append(self.compileExpression())

        ele.append(self._createSpecifiedElement(Symbol.SEMICOLON.value))
        return ele

    def compileExpression(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.EXPRESSION)
        ele.append(self.compileTerm())
        while self.tokenizer.current_token in OP:
            ele.append(self._createCurrentTokenElement())
            ele.append(self.compileTerm())
        return ele

    def compileExpressionList(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.EXPRESSION_LIST)
        if self.tokenizer.current_token == Symbol.RPAREN.value:
            return ele

        ele.append(self.compileExpression())
        while self.tokenizer.current_token == Symbol.COMMA.value:
            ele.append(self._createSpecifiedElement(Symbol.COMMA.value))
            ele.append(self.compileExpression())
        return ele

    def compileTerm(self) -> Element:
        ele = self._createNonTerminalElement(ElementTag.TERM)
        if self.tokenizer.tokenType() in (TokenType.INT_CONST, TokenType.STRING_CONST):
            ele.append(self._createCurrentTokenElement())
            return ele

        if self.tokenizer.current_token in KEYWORD_CONSTANT:
            ele.append(self._createCurrentTokenElement())
            return ele

        if self.tokenizer.current_token == Symbol.LPAREN.value:
            ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))
            ele.append(self.compileExpression())
            ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
            return ele

        if self.tokenizer.current_token in UNARY_OP:
            ele.append(self._createCurrentTokenElement())
            ele.append(self.compileTerm())
            return ele

        if self.tokenizer.tokenType() != TokenType.IDENTIFIER:
            raise Exception(f"Invalid syntax {self.tokenizer.current_token}")

        # 先読みが必要なもの
        ele.append(self._createCurrentTokenElement())
        if self.tokenizer.current_token == Symbol.LBRACKET.value:
            ele.append(self._createSpecifiedElement(Symbol.LBRACKET.value))
            ele.append(self.compileExpression())
            ele.append(self._createSpecifiedElement(Symbol.RBRACKET.value))
        elif self.tokenizer.current_token == Symbol.LPAREN.value:
            ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))
            ele.append(self.compileExpressionList())
            ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
        elif self.tokenizer.current_token == Symbol.DOT.value:
            ele.append(self._createSpecifiedElement(Symbol.DOT.value))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))
            ele.append(self._createSpecifiedElement(Symbol.LPAREN.value))
            ele.append(self.compileExpressionList())
            ele.append(self._createSpecifiedElement(Symbol.RPAREN.value))
        return ele

    def _compileType(self) -> Element:
        if (
            self.tokenizer.tokenType() == TokenType.KEYWORD
            and self.tokenizer.current_token in PRIMITIVE_TYPE
        ):
            return self._createCurrentTokenElement()

        if self.tokenizer.tokenType() == TokenType.IDENTIFIER:
            return self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER)

        raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

    def _createSpecifiedTokenTypeElement(self, tokenType: TokenType) -> Element:
        if self.tokenizer.tokenType() != tokenType:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")
        return self._createCurrentTokenElement()

    def _createCurrentTokenElement(self) -> Element:
        token_tag = self.tokenizer.tokenType().value
        text = self._currentTokenValue()
        ele = self._createTerminalElement(token_tag, text)

        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        return ele

    def _createSpecifiedElement(self, token: str) -> Element:
        if self.tokenizer.current_token != token:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createCurrentTokenElement()
        return ele

    def _createNonTerminalElement(self, tag: ElementTag) -> Element:
        ele = Element(tag.value)
        ele.tail = "\n"
        return ele

    def _createTerminalElement(self, tag: str, text: str) -> Element:
        ele = Element(tag)
        ele.tail = "\n"
        ele.text = f" {text} "
        return ele

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
