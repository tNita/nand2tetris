from jack_tokenizer import JackTokenizer, TokenType, KeyWord
from xml.etree.ElementTree import Element
from typing import Optional


class CompilationEngine:
    def __init__(self, tokenizer: JackTokenizer) -> None:
        self.tokenizer = tokenizer
        self.tokenizer.advance()

    def compileClass(self) -> Element:
        ele = self._createXMLElement("class")

        ele.append(self._createSpecifiedElement(KeyWord.CLASS.value))
        ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))
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
        ele.append(self._createSpecifiedElement(self.tokenizer.current_token))
        ele.append(self._compileType())
        ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

        while self.tokenizer.current_token == ",":
            ele.append(self._createSpecifiedElement(","))
            ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

        ele.append(self._createSpecifiedElement(";"))
        return ele

    def compileSubroutine(self) -> Element:
        if self.tokenizer.current_token not in ("constructor", "function", "method"):
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

        ele = self._createXMLElement("subroutineDec")
        ele.append(self._createSpecifiedElement(self.tokenizer.current_token))
        if self.tokenizer.current_token == "void":
            ele.append(self._createSpecifiedElement(self.tokenizer.current_token))
        else:
            ele.append(self._compileType())
        ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))
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
            ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

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
        ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

        while self.tokenizer.current_token == ",":
            ele.append(self._createSpecifiedElement(","))
            ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

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
        ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

        if self.tokenizer.current_token == "[":
            raise Exception("Array is unsupported")

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
        ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

        if self.tokenizer.current_token == ".":
            ele.append(self._createSpecifiedElement("."))
            ele.append(self._createSpecifiedTypeElement(TokenType.IDENTIFIER))

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
        raise NotImplementedError("Expression compilation is not implemented yet")

    def compileExpressionList(self) -> Element:
        raise NotImplementedError("Expression list compilation is not implemented yet")

    def compileTerm(self) -> Element:
        raise NotImplementedError("Term compilation is not implemented yet")

    def _compileType(self) -> Element:
        if (
            self.tokenizer.tokenType() == TokenType.KEYWORD
            and self.tokenizer.current_token
            in (
                "int",
                "char",
                "boolean",
            )
        ):
            return self._createSpecifiedElement(self.tokenizer.current_token)

        if self.tokenizer.tokenType() == TokenType.IDENTIFIER:
            return self._createSpecifiedTypeElement(TokenType.IDENTIFIER)

        raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")

    def _createSpecifiedTypeElement(self, token_type: TokenType) -> Element:
        if self.tokenizer.tokenType() != token_type:
            raise Exception(f"Invalid syntax: {self.tokenizer.current_token}")
        return self._createSpecifiedElement(self.tokenizer.current_token)

    def _createSpecifiedElement(self, token: str) -> Element:
        if self.tokenizer.current_token != token:
            raise Exception(f"Invalid syntax: expected {self.tokenizer.current_token}")

        ele = self._createXMLElement(
            self.tokenizer.tokenType().value, self.tokenizer.current_token
        )
        self.tokenizer.advance()
        return ele

    def _createXMLElement(self, tag: str, text: Optional[str] = None) -> Element:
        ele = Element(tag)
        ele.tail = "\n"
        if text is not None:
            ele.text = f" {text}"
        return ele
