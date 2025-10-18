import os
import sys
from typing import Iterable
from xml.etree.ElementTree import Element, ElementTree, SubElement

from jack_tokenizer import JackTokenizer, TokenType


def collect_jack_files(input_path: str) -> list[str]:
    resolved = os.path.abspath(input_path)

    if os.path.isdir(resolved):
        jack_files = [
            os.path.join(resolved, name)
            for name in sorted(os.listdir(resolved))
            if name.endswith(".jack") and os.path.isfile(os.path.join(resolved, name))
        ]
        if not jack_files:
            raise Exception("No jack files found in the directory")
        return jack_files

    if resolved.endswith(".jack") and os.path.isfile(resolved):
        return [resolved]

    if resolved.endswith(".jack"):
        raise Exception("Specified jack file does not exist")

    raise Exception("Please specify a jack file or directory")


def _token_to_value(tokenizer: JackTokenizer, token_type: TokenType) -> str:
    if token_type == TokenType.KEYWORD:
        return tokenizer.keyWord().value
    if token_type == TokenType.SYMBOL:
        return tokenizer.symbol()
    if token_type == TokenType.IDENTIFIER:
        return tokenizer.identifier()
    if token_type == TokenType.INT_CONST:
        return str(tokenizer.intVal())
    if token_type == TokenType.STRING_CONST:
        return tokenizer.stringVal()
    raise Exception(f"Unsupported token type: {token_type}")


def tokenize_file(jack_path: str) -> str:
    tokenizer = JackTokenizer(jack_path)
    output_path = jack_path[:-5] + "T.xml"

    root = Element("tokens")
    root.text = "\n"

    while tokenizer.hasMoreTokens():
        tokenizer.advance()
        token_type = tokenizer.tokenType()
        value = _token_to_value(tokenizer, token_type)

        token_elem = SubElement(root, token_type.value)
        token_elem.text = f" {value} "
        token_elem.tail = "\n"

    tree = ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=False)

    with open(output_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        for line in lines:
            f.write(line + "\r\n")

    return output_path


def process_files(jack_files: Iterable[str]) -> None:
    for jack_path in jack_files:
        output_path = tokenize_file(jack_path)
        print(f"Tokenized: {output_path}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python jack_analyzer.py <jack file or directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    jack_files = collect_jack_files(input_path)
    process_files(jack_files)


if __name__ == "__main__":
    main()
