from typing import Literal
from parser import CommandType
import os


CALC_COMMAND = {
    "add": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M+D"],
    "sub": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M-D"],
    "neg": ["@SP", "A=M-1", "M=-M"],
    "and": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M&D"],
    "or": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M|D"],
    "not": ["@SP", "A=M-1", "M=!M"],
}

COMPARE_COMMAND = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}

# TODO: 名前変える
FIXED_MEMORY_SEGMENT = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

PUSH_ASM = ["@SP", "A=M", "M=D", "@SP", "M=M+1"]

POP_ASM = ["@SP", "AM=M-1", "D=M"]


class CodeWriter:
    def __init__(self, output_file: str, vm_file: str):
        self.output_file = output_file
        self.file = open(output_file, "w")
        self.label_counter = 0
        self.current_file_name = os.path.basename(vm_file).replace(".vm", "")

    def writeArithmetic(self, command: str) -> None:
        if command in CALC_COMMAND:
            self.write(CALC_COMMAND[command])
        elif command in COMPARE_COMMAND:
            self.write(self.compareAsm(COMPARE_COMMAND[command]))
        else:
            raise Exception()

    def compareAsm(self, jump: str) -> list[str]:
        label_true = f"EQ_TRUE_{self.label_counter}"
        label_end = f"EQ_END_{self.label_counter}"
        self.label_counter += 1
        return [
            "@SP",
            "AM=M-1",
            "D=M",
            "A=A-1",
            "D=M-D",
            f"@{label_true}",
            f"D;{jump}",
            "@SP",
            "A=M-1",
            "M=0",
            f"@{label_end}",
            "0;JMP",
            f"({label_true})",
            "@SP",
            "A=M-1",
            "M=-1",
            f"({label_end})",
        ]

    def writePushPop(
        self,
        commandType: Literal[CommandType.C_POP, CommandType.C_PUSH],
        segment: str,
        index: int,
    ) -> None:
        if commandType == CommandType.C_PUSH:
            self.write(self.pushAsm(segment, index))
        elif commandType == CommandType.C_POP:
            self.write(self.popAsm(segment, index))

    def pushAsm(self, segment: str, index: int) -> list[str]:
        # pushしたい値をDに入れた上でスタックマシンにpush
        if segment in FIXED_MEMORY_SEGMENT:
            base = FIXED_MEMORY_SEGMENT[segment]
            return [
                f"@{index}",
                "D=A",
                f"@{base}",
                "A=M+D",
                "D=M",
            ] + PUSH_ASM
        elif segment == "pointer":
            if index > 1:
                raise Exception()
            base = "THIS" if index == 0 else "THAT"
            return [f"@{base}", "D=M"] + PUSH_ASM
        elif segment == "temp":
            if index > 7:
                raise Exception()
            return [f"@{5 + index}", "D=M"] + PUSH_ASM

        elif segment == "constant":
            return [f"@{index}", "D=A"] + PUSH_ASM
        elif segment == "static":
            return [f"@{self.current_file_name}.{index}", "D=M"] + PUSH_ASM
        else:
            raise Exception(f"Unsupported segment: {segment}")

    def popAsm(self, segment: str, index: int) -> list[str]:
        # popした値を指定したメモリに格納
        if segment in FIXED_MEMORY_SEGMENT:
            base = FIXED_MEMORY_SEGMENT[segment]
            return (
                [
                    f"@{index}",
                    "D=A",
                    f"@{base}",
                    "A=M+D",
                    "@R13",
                    "M=A",
                ]
                + POP_ASM
                + ["@R13", "A=M", "M=D"]
            )
        elif segment == "pointer":
            if index > 1:
                raise Exception()
            base = "THIS" if index == 0 else "THAT"
            return POP_ASM + [f"@{base}", "M=D"]
        elif segment == "temp":
            if index > 7:
                raise Exception()
            return POP_ASM + [f"@{5 + index}", "M=D"]
        elif segment == "static":
            return POP_ASM + [f"@{self.current_file_name}.{index}", "M=D"]
        else:
            raise Exception(
                f"Unsupported segment: {segment} (constant cannot be popped)"
            )

    def write(self, asms: list[str]) -> None:
        for a in asms:
            self.file.write(a + "\n")

    def close(self):
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
