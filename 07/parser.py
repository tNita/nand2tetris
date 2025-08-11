from enum import Enum


class CommandType(Enum):
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3


# VMコマンドの構文解析を行う（文法チェックは行わない）
class Parser:
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.file = None
        self.current_line: str | None = None

    def hasMoreLines(self) -> bool:
        pos = self.file.tell()
        # 1行読んでみる
        line = self.file.readline()
        # ファイルポインタを元の位置に戻す
        self.file.seek(pos)
        # 空文字列（EOF）でなければTrue
        return bool(line)

    def advance(self) -> None:
        while True:
            if not self.hasMoreLines():
                # EOF
                self.current_line = None
                return None

            line = self.file.readline()
            # コメントと前後の空白を除去
            cleaned = line.split("//", 1)[0].strip()
            if not cleaned:
                # 空行またはコメントのみの行はスキップ
                continue

            self.current_line = cleaned
            return None

    def commandType(self) -> CommandType:
        command = self.current_line.split()[0]

        if command in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return CommandType.C_ARITHMETIC
        elif command == "push":
            return CommandType.C_PUSH
        elif command == "pop":
            return CommandType.C_POP
        else:
            raise Exception(f"Unsupported command: {command}")

    def arg1(self) -> str:
        command_type = self.commandType()
        if command_type == CommandType.C_ARITHMETIC:
            return self.current_line.split()[0]
        elif command_type in [CommandType.C_PUSH, CommandType.C_POP]:
            return self.current_line.split()[1]
        else:
            raise Exception("arg1() called for invalid command type")

    def arg2(self) -> int:
        if self.commandType() in [CommandType.C_PUSH, CommandType.C_POP]:
            return int(self.current_line.split()[2])

    def close(self) -> None:
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def __enter__(self):
        self.file = open(self.filename, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
