import io
import os
import sys
from typing import Iterable
from xml.etree.ElementTree import Element

from compilation_engine import CompilationEngine
from jack_tokenizer import JackTokenizer


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


# テストの都合に合わせてXMLにインデントを設ける
def _indent(element: Element, level: int = 0) -> None:
    indent = "\n" + "  " * level
    if len(element):
        if not element.text or not element.text.strip():
            element.text = indent + "  "
        for index, child in enumerate(element):
            _indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent + "  "
            if index == len(element) - 1 and child.tail == indent + "  ":
                child.tail = indent
        if not element.tail or not element.tail.strip():
            element.tail = indent
    else:
        if not element.text or not element.text.strip():
            element.text = indent
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indent


def compile_file(jack_path: str) -> None:
    tokenizer = JackTokenizer(jack_path)
    engine = CompilationEngine(tokenizer, jack_path[:-5] + ".vm")
    engine.compileClass()


def process_files(jack_files: Iterable[str]) -> None:
    for jack_path in jack_files:
        compile_file(jack_path)
        print(f"Compiled: {jack_path}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python jack_analyzer.py <jack file or directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    jack_files = collect_jack_files(input_path)
    process_files(jack_files)


if __name__ == "__main__":
    main()
