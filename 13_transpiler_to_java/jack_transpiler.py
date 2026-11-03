"""Transpile a Jack file or directory to runnable Java source files."""

import argparse
from pathlib import Path
import sys
from typing import Optional

from jack_parser import TranspileError, parse_file
from java_writer import JavaWriter, Program, java_class


def collect_jack_files(input_path: Path) -> list[Path]:
    if input_path.is_file() and input_path.suffix == ".jack":
        return [input_path]
    if input_path.is_dir():
        files = sorted(input_path.glob("*.jack"))
        files = [path for path in files if path.is_file()]
        if files:
            return files
        raise TranspileError(f"{input_path}: No .jack files found")
    raise TranspileError(f"{input_path}: Specify an existing .jack file or directory")


def transpile(input_path: Path, output_dir: Optional[Path] = None) -> list[Path]:
    input_path = Path(input_path)
    files = collect_jack_files(input_path)
    destination = Path(output_dir) if output_dir is not None else files[0].parent
    classes = [parse_file(path) for path in files]
    program = Program(classes)
    # Validate every source before creating output, so syntax errors do not
    # leave behind a partially converted project.
    generated = {
        java_class(cls.name.text) + ".java": JavaWriter(program, cls).write()
        for cls in classes
    }
    runtime = Path(__file__).resolve().parent / "runtime" / "JackRuntime.java"
    runtime_source = runtime.read_text(encoding="utf-8")
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for name, source in generated.items():
        target = destination / name
        target.write_text(source, encoding="utf-8")
        written.append(target)
    runtime_target = destination / "JackRuntime.java"
    if runtime_target.resolve() != runtime.resolve():
        runtime_target.write_text(runtime_source, encoding="utf-8")
    written.append(runtime_target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Transpile Jack source code to Java")
    parser.add_argument("input", type=Path, help=".jack file or directory (non-recursive)")
    parser.add_argument("-o", "--output-dir", type=Path, help="output directory (default: input directory)")
    arguments = parser.parse_args()
    try:
        for path in transpile(arguments.input, arguments.output_dir):
            print(f"Generated: {path}")
    except (TranspileError, OSError, UnicodeError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
