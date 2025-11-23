from enum import Enum


class CommandType(Enum):
    C_ARITHMETIC = 1
    C_PUSH = 2
    C_POP = 3
    C_LABEL = 4
    C_GOTO = 5
    C_IF = 6
    C_FUNCTION = 7
    C_RETURN = 8
    C_CALL = 9


COMMAND_TYPE_MAP = {
    "add": CommandType.C_ARITHMETIC,
    "sub": CommandType.C_ARITHMETIC,
    "neg": CommandType.C_ARITHMETIC,
    "eq": CommandType.C_ARITHMETIC,
    "gt": CommandType.C_ARITHMETIC,
    "lt": CommandType.C_ARITHMETIC,
    "and": CommandType.C_ARITHMETIC,
    "or": CommandType.C_ARITHMETIC,
    "not": CommandType.C_ARITHMETIC,
    "push": CommandType.C_PUSH,
    "pop": CommandType.C_POP,
    "label": CommandType.C_LABEL,
    "goto": CommandType.C_GOTO,
    "if-goto": CommandType.C_IF,
    "function": CommandType.C_FUNCTION,
    "return": CommandType.C_RETURN,
    "call": CommandType.C_CALL,
}


# VMコマンドの構文解析を行う（文法チェックは行わない）
class Parser:
    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
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

        if command in COMMAND_TYPE_MAP:
            return COMMAND_TYPE_MAP[command]
        else:
            raise Exception(f"called for unsupported command: {command}")

    def arg1(self) -> str:
        command_type = self.commandType()
        if command_type == CommandType.C_ARITHMETIC:
            return self.current_line.split()[0]
        if command_type != CommandType.C_RETURN:
            return self.current_line.split()[1]
        raise Exception("called for invalid command type")

    def arg2(self) -> int:
        if self.commandType() in [
            CommandType.C_PUSH,
            CommandType.C_POP,
            CommandType.C_FUNCTION,
            CommandType.C_CALL,
        ]:
            return int(self.current_line.split()[2])
        raise Exception("called for invalid command type")

    def close(self) -> None:
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def __enter__(self):
        self.file = open(self.filepath, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
