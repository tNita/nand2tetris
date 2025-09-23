import os
import sys

from parser import Parser, CommandType
from codewriter import CodeWriter


def collect_vm_files(input_path: str) -> tuple[list[str], str]:
    resolved = os.path.abspath(input_path)

    if os.path.isdir(resolved):
        vm_files = sorted(
            os.path.join(resolved, name)
            for name in os.listdir(resolved)
            if name.endswith(".vm") and os.path.isfile(os.path.join(resolved, name))
        )
        if not vm_files:
            raise Exception("No vm files found in the directory")
        directory_name = os.path.basename(resolved)
        output_file = os.path.join(resolved, f"{directory_name}.asm")
        return vm_files, output_file

    if resolved.endswith(".vm") and os.path.isfile(resolved):
        output_file = resolved[:-3] + ".asm"
        return [resolved], output_file

    if resolved.endswith(".vm"):
        raise Exception("Specified vm file does not exist")

    raise Exception("Please specify a vm file or directory")


def translate_file(code_writer: CodeWriter, vm_path: str) -> None:
    code_writer.setFileName(os.path.basename(vm_path))
    with Parser(vm_path) as parser:
        while parser.hasMoreLines():
            parser.advance()
            if parser.current_line is None:
                break

            command_type = parser.commandType()
            code_writer.write([f"// {parser.current_line}"])

            if command_type == CommandType.C_ARITHMETIC:
                code_writer.writeArithmetic(parser.arg1())
            elif command_type in (CommandType.C_PUSH, CommandType.C_POP):
                segment = parser.arg1()
                index = parser.arg2()
                code_writer.writePushPop(command_type, segment, index)
            elif command_type == CommandType.C_LABEL:
                code_writer.writeLabel(parser.arg1())
            elif command_type == CommandType.C_GOTO:
                code_writer.writeGoto(parser.arg1())
            elif command_type == CommandType.C_IF:
                code_writer.writeIf(parser.arg1())
            elif command_type == CommandType.C_FUNCTION:
                code_writer.writeFunction(parser.arg1(), parser.arg2())
            elif command_type == CommandType.C_CALL:
                code_writer.writeCall(parser.arg1(), parser.arg2())
            elif command_type == CommandType.C_RETURN:
                code_writer.writeReturn()
            else:
                raise Exception(f"Unsupported command: {parser.current_line}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python vmtranslator.py <vm file or directory>")
        sys.exit(1)
    input_path = sys.argv[1]
    vm_files, output_file = collect_vm_files(input_path)
    with CodeWriter(output_file, os.path.basename(vm_files[0])) as code_writer:
        if any(os.path.basename(path) == "Sys.vm" for path in vm_files):
            code_writer.writeBootstrap()
        for vm_path in vm_files:
            translate_file(code_writer, vm_path)

    print(f"Translation completed: {output_file}")


if __name__ == "__main__":
    main()
