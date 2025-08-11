import sys
import os
from parser import Parser, CommandType
from codewriter import CodeWriter


def main():
    if len(sys.argv) != 2:
        print("使用法: python vmtranslator.py <vmファイル>")
        sys.exit(1)

    input_path = sys.argv[1]

    # .vmファイルのみ受け付ける
    if not input_path.endswith(".vm"):
        print("エラー: .vmファイルを指定してください")
        sys.exit(1)
    
    if not os.path.isfile(input_path):
        print("エラー: ファイルが存在しません")
        sys.exit(1)

    output_file = input_path.replace(".vm", ".asm")

    # CodeWriterを初期化
    with CodeWriter(output_file, input_path) as code_writer:
        # パーサーでVMファイルを解析
        with Parser(input_path) as parser:
            while parser.hasMoreLines():
                parser.advance()

                if parser.current_line is None:
                    break

                command_type = parser.commandType()

                if command_type == CommandType.C_ARITHMETIC:
                    code_writer.writeArithmetic(parser.arg1())
                elif command_type in [CommandType.C_PUSH, CommandType.C_POP]:
                    segment = parser.arg1()
                    index = int(parser.arg2())
                    code_writer.writePushPop(command_type, segment, index)

    print(f"変換が完了しました: {output_file}")


if __name__ == "__main__":
    main()