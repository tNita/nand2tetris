from enum import Enum


class InstructionType(Enum):
    A_INSTRUCTION = 1
    C_INSTRUCTION = 2
    L_INSTRUCTION = 3


# NOTE: ここでは文法的に良いかのチェックはしない
class Parser:
    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.file = open(filename, "r")
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

    def instructionType(self) -> InstructionType:
        if self.current_line[0] == "@":
            return InstructionType.A_INSTRUCTION
        elif self.current_line.startswith("(") and self.current_line.endswith(")"):
            return InstructionType.L_INSTRUCTION
        return InstructionType.C_INSTRUCTION

    def symbol(self) -> str:
        if self.instructionType() == InstructionType.A_INSTRUCTION:
            return self.current_line[1:]
        elif self.instructionType() == InstructionType.L_INSTRUCTION:
            return self.current_line.strip("()")
        else:
            raise Exception()

    def dest(self) -> str:
        if self.instructionType() != InstructionType.C_INSTRUCTION:
            raise Exception()
        if "=" not in self.current_line:
            return "null"
        return self.current_line.split("=")[0]

    def comp(self) -> str:
        if self.instructionType() != InstructionType.C_INSTRUCTION:
            raise Exception()

        clean = self.current_line.split(";")[0]
        if "=" in clean:
            return clean.split("=")[1]
        return clean

    def jump(self) -> str:
        if self.instructionType() != InstructionType.C_INSTRUCTION:
            raise Exception()

        if ";" not in self.current_line:
            return "null"
        return self.current_line.split(";")[1]

    def close(self) -> None:
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()
