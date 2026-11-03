import io
import os
import sys
import tempfile
from typing import Iterable, Optional
from xml.etree.ElementTree import Element

from compilation_engine import CompilationEngine
from jack_tokenizer import JackTokenizer
from type_checker import TypeCheckError, TypeRegistry


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


def compile_file(jack_path: str, registry: Optional[TypeRegistry] = None) -> None:
    jack_path = os.path.abspath(jack_path)
    if registry is None:
        registry = TypeRegistry.from_files(collect_jack_files(os.path.dirname(jack_path)))
    tokenizer = JackTokenizer(jack_path)
    # A rejected source must not overwrite an existing VM file with partial code.
    with tempfile.NamedTemporaryFile(
        dir=os.path.dirname(jack_path), suffix=".vm", delete=False
    ) as output:
        temp_path = output.name
    try:
        engine = CompilationEngine(tokenizer, temp_path, registry)
        try:
            engine.compileClass()
        finally:
            engine.vmWriter.close()
        os.replace(temp_path, jack_path[:-5] + ".vm")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def process_files(jack_files: Iterable[str]) -> None:
    jack_files = list(jack_files)
    registry = TypeRegistry.from_files(jack_files)
    for jack_path in jack_files:
        compile_file(jack_path, registry)
        print(f"Compiled: {jack_path}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python jack_analyzer.py <jack file or directory>")
        sys.exit(1)

    input_path = sys.argv[1]
    jack_files = collect_jack_files(input_path)
    try:
        if os.path.isfile(input_path):
            compile_file(jack_files[0])
            print(f"Compiled: {jack_files[0]}")
        else:
            process_files(jack_files)
    except TypeCheckError as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
