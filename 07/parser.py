from enum import Enum


class CommandType(Enum):
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3


# NOTE: ここでは文法的に良いかのチェックはしない
class Parser:
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.file = None
        self.current_line: str | None = None

    def hasMoreLines(self) -> bool:
        pos = self.file.tell()
        # １行読んでみる
        line = self.file.readline()
        # 元の位置へ戻す
        self.file.seek(pos)
        # line が空文字列(""＝EOF) でなければ True
        return bool(line)

    def advance(self) -> None:
        while True:
            if not self.hasMoreLines():
                # EOF
                self.current_line = None
                return None

            line = self.file.readline()
            # コメントと空白を除去
            cleaned = line.split("//", 1)[0].strip()
            if not cleaned:
                # 空白行／コメントだけの行 → 次のループへ
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
            raise Exception(f"サポート外のコマンド {command}")

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
            return self.current_line.split()[2]

    def close(self) -> None:
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def __enter__(self):
        self.file = open(self.filename, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
