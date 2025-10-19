from jack_tokenizer import JackTokenizer, TokenType, KeyWord
from xml.etree.ElementTree import Element
from typing import Optional

PRIMITIVE_TYPE = ("int", "char", "boolean")

OP = ("+", "-", "*", "/", "&", "|", "<", ">", "=")
UNARY_OP = ("-", "~")

KEYWORD_CONSTANT = ("true", "false", "null", "this")


class CompilationEngine:
    def __init__(self, tokenizer: JackTokenizer) -> None:
        self.tokenizer = tokenizer
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        else:
            raise Exception(f"this file is empty")

    def compileClass(self) -> Element:
        ele = self._createXMLElement("class")

        ele.append(self._createSpecifiedElement(KeyWord.CLASS.value))
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))
        ele.append(self._createSpecifiedElement("{"))

        while self.tokenizer.current_token in ("static", "field"):
            ele.append(self.compileClassVarDec())

        while self.tokenizer.current_token in ("constructor", "function", "method"):
            ele.append(self.compileSubroutine())

        ele.append(self._createSpecifiedElement("}"))
        return ele

    def compileClassVarDec(self) -> Element:
        if self.tokenizer.current_token not in ("static", "field"):
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createXMLElement("classVarDec")
        ele.append(self._createCurrentTokenElement())
        ele.append(self._compileType())
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        while self.tokenizer.current_token == ",":
            ele.append(self._createSpecifiedElement(","))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement(";"))
        return ele

    def compileSubroutine(self) -> Element:
        if self.tokenizer.current_token not in ("constructor", "function", "method"):
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createXMLElement("subroutineDec")
        ele.append(self._createCurrentTokenElement())
        if self.tokenizer.current_token == "void":
            ele.append(self._createCurrentTokenElement())
        else:
            ele.append(self._compileType())
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))
        ele.append(self._createSpecifiedElement("("))

        ele.append(self.compileParameterList())
        ele.append(self._createSpecifiedElement(")"))
        ele.append(self.compileSubroutineBody())
        return ele

    def compileParameterList(self) -> Element:
        ele = self._createXMLElement("parameterList")

        if self.tokenizer.current_token == ")":
            return ele

        while True:
            ele.append(self._compileType())
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

            if self.tokenizer.current_token != ",":
                break

            ele.append(self._createSpecifiedElement(","))

        return ele

    def compileSubroutineBody(self) -> Element:
        ele = self._createXMLElement("subroutineBody")
        ele.append(self._createSpecifiedElement("{"))

        while self.tokenizer.current_token == "var":
            ele.append(self.compileVarDec())

        ele.append(self.compileStatements())
        ele.append(self._createSpecifiedElement("}"))
        return ele

    def compileVarDec(self) -> Element:
        if self.tokenizer.current_token != "var":
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createXMLElement("varDec")
        ele.append(self._createSpecifiedElement("var"))
        ele.append(self._compileType())
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        while self.tokenizer.current_token == ",":
            ele.append(self._createSpecifiedElement(","))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement(";"))
        return ele

    def compileStatements(self) -> Element:
        ele = self._createXMLElement("statements")

        while self.tokenizer.current_token in ("let", "if", "while", "do", "return"):
            if self.tokenizer.current_token == "let":
                ele.append(self.compileLet())
            elif self.tokenizer.current_token == "if":
                ele.append(self.compileIf())
            elif self.tokenizer.current_token == "while":
                ele.append(self.compileWhile())
            elif self.tokenizer.current_token == "do":
                ele.append(self.compileDo())
            else:
                ele.append(self.compileReturn())

        return ele

    def compileLet(self) -> Element:
        ele = self._createXMLElement("letStatement")
        ele.append(self._createSpecifiedElement("let"))
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        if self.tokenizer.current_token == "[":
            ele.append(self._createSpecifiedElement("["))
            ele.append(self.compileExpression())
            ele.append(self._createSpecifiedElement("]"))

        ele.append(self._createSpecifiedElement("="))
        ele.append(self.compileExpression())
        ele.append(self._createSpecifiedElement(";"))
        return ele

    def compileIf(self) -> Element:
        ele = self._createXMLElement("ifStatement")
        ele.append(self._createSpecifiedElement("if"))
        ele.append(self._createSpecifiedElement("("))
        ele.append(self.compileExpression())
        ele.append(self._createSpecifiedElement(")"))
        ele.append(self._createSpecifiedElement("{"))
        ele.append(self.compileStatements())
        ele.append(self._createSpecifiedElement("}"))

        if self.tokenizer.current_token == "else":
            ele.append(self._createSpecifiedElement("else"))
            ele.append(self._createSpecifiedElement("{"))
            ele.append(self.compileStatements())
            ele.append(self._createSpecifiedElement("}"))

        return ele

    def compileWhile(self) -> Element:
        ele = self._createXMLElement("whileStatement")
        ele.append(self._createSpecifiedElement("while"))
        ele.append(self._createSpecifiedElement("("))
        ele.append(self.compileExpression())
        ele.append(self._createSpecifiedElement(")"))
        ele.append(self._createSpecifiedElement("{"))
        ele.append(self.compileStatements())
        ele.append(self._createSpecifiedElement("}"))
        return ele

    def compileDo(self) -> Element:
        ele = self._createXMLElement("doStatement")
        ele.append(self._createSpecifiedElement("do"))
        ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        if self.tokenizer.current_token == ".":
            ele.append(self._createSpecifiedElement("."))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement("("))
        ele.append(self.compileExpressionList())
        ele.append(self._createSpecifiedElement(")"))
        ele.append(self._createSpecifiedElement(";"))
        return ele

    def compileReturn(self) -> Element:
        ele = self._createXMLElement("returnStatement")
        ele.append(self._createSpecifiedElement("return"))

        if self.tokenizer.current_token != ";":
            ele.append(self.compileExpression())

        ele.append(self._createSpecifiedElement(";"))
        return ele

    def compileExpression(self) -> Element:
        ele = self._createXMLElement("expression")
        ele.append(self.compileTerm())
        while self.tokenizer.current_token in OP:
            ele.append(self._createCurrentTokenElement())
            ele.append(self.compileTerm())
        return ele

    def compileExpressionList(self) -> Element:
        ele = self._createXMLElement("expressionList")
        if self.tokenizer.current_token == ")":
            return ele

        ele.append(self.compileExpression())
        while self.tokenizer.current_token == ",":
            ele.append(self._createSpecifiedElement(","))
            ele.append(self.compileExpression())
        return ele

    def compileTerm(self) -> Element:
        ele = self._createXMLElement("term")
        if self.tokenizer.tokenType() in (TokenType.INT_CONST, TokenType.STRING_CONST):
            ele.append(self._createCurrentTokenElement())
            return ele

        if self.tokenizer.current_token in KEYWORD_CONSTANT:
            ele.append(self._createCurrentTokenElement())
            return ele

        if self.tokenizer.current_token == "(":
            ele.append(self._createSpecifiedElement("("))
            ele.append(self.compileExpression())
            ele.append(self._createSpecifiedElement(")"))
            return ele

        if self.tokenizer.current_token in UNARY_OP:
            ele.append(self._createCurrentTokenElement())
            ele.append(self.compileTerm())
            return ele

        if self.tokenizer.tokenType() != TokenType.IDENTIFIER:
            raise Exception(f"Invalid syntax {self.tokenizer.current_token}")

        # 先読みが必要なもの
        ele.append(self._createCurrentTokenElement())
        if self.tokenizer.current_token == "[":
            ele.append(self._createSpecifiedElement("["))
            ele.append(self.compileExpression())
            ele.append(self._createSpecifiedElement("]"))
        elif self.tokenizer.current_token == "(":
            ele.append(self._createSpecifiedElement("("))
            ele.append(self.compileExpressionList())
            ele.append(self._createSpecifiedElement(")"))
        elif self.tokenizer.current_token == ".":
            ele.append(self._createSpecifiedElement("."))
            ele.append(self._createSpecifiedTokenTypeElement(TokenType.IDENTIFIER))
            ele.append(self._createSpecifiedElement("("))
            ele.append(self.compileExpressionList())
            ele.append(self._createSpecifiedElement(")"))
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
        ele = self._createXMLElement(
            self.tokenizer.tokenType().value, self._currentTokenValue()
        )
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()
        return ele

    def _createSpecifiedElement(self, token: str) -> Element:
        if self.tokenizer.current_token != token:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createCurrentTokenElement()
        return ele

    def _createXMLElement(self, tag: str, text: Optional[str] = None) -> Element:
        ele = Element(tag)
        ele.tail = "\n"
        if text is not None:
            ele.text = f" {text} "
        return ele

    def _createTokenElement(self, tokenType: TokenType, value: str) -> Element:
        return self._createXMLElement(tokenType.value, value)

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
