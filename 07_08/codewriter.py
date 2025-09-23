from typing import Literal
from parser import CommandType
import os


CALC_COMMAND = {
    "add": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D+M"],
    "sub": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=M-D"],
    "neg": ["@SP", "A=M-1", "M=-M"],
    "and": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D&M"],
    "or": ["@SP", "AM=M-1", "D=M", "A=A-1", "M=D|M"],
    "not": ["@SP", "A=M-1", "M=!M"],
}

COMPARE_COMMAND = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}

# メモリセグメントの基底アドレス
FIXED_MEMORY_SEGMENT = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

PUSH_ASM = ["@SP", "A=M", "M=D", "@SP", "M=M+1"]

POP_ASM = ["@SP", "AM=M-1", "D=M"]


class CodeWriter:
    def __init__(self, output_file: str, fileName: str):
        self.output_file = output_file
        self.file = open(output_file, "w")
        self.label_counter = 0
        self.return_counter = 0
        self.currentFile, _ = os.path.splitext(fileName)
        self.currentFunction = None

    def writeBootstrap(self) -> None:
        self.write(["@256", "D=A", "@SP", "M=D"])
        self.writeCall("Sys.init", 0)

    def writeArithmetic(self, command: str) -> None:
        if command in CALC_COMMAND:
            self.write(CALC_COMMAND[command])
        elif command in COMPARE_COMMAND:
            self.write(self.compareAsm(COMPARE_COMMAND[command]))
        else:
            raise Exception()

    def compareAsm(self, jump: str) -> list[str]:
        label_true = f"COMP_TRUE_{self.label_counter}"
        label_end = f"COMP_END_{self.label_counter}"
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
            "M=-1",  # 全ビットtrue
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
        # 指定されたセグメントの値をスタックにプッシュするASMコードを生成
        if segment in FIXED_MEMORY_SEGMENT:
            base = FIXED_MEMORY_SEGMENT[segment]
            return [
                f"@{index}",
                "D=A",
                f"@{base}",
                "A=D+M",
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
            return [f"@{self.currentFile}.{index}", "D=M"] + PUSH_ASM
        else:
            raise Exception(f"Unsupported segment: {segment}")

    def popAsm(self, segment: str, index: int) -> list[str]:
        # スタックからポップした値を指定されたセグメントに格納するASMを生成
        if segment in FIXED_MEMORY_SEGMENT:
            base = FIXED_MEMORY_SEGMENT[segment]
            return (
                [
                    f"@{index}",
                    "D=A",
                    f"@{base}",
                    "D=D+M",
                    "@R13",
                    "M=D",
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
            return POP_ASM + [f"@{self.currentFile}.{index}", "M=D"]
        else:
            raise Exception(
                f"Unsupported segment: {segment} (constant cannot be popped)"
            )

    def writeLabel(self, label: str) -> None:
        self.write([f"({self._scopedLabel(label)})"])

    def writeGoto(self, label: str) -> None:
        self.write([f"@{self._scopedLabel(label)}", "0;JMP"])

    def writeIf(self, label: str) -> None:
        asm = POP_ASM + [f"@{self._scopedLabel(label)}", "D;JNE"]
        self.write(asm)

    def _scopedLabel(self, label: str) -> str:
        if self.currentFunction:
            return f"{self.currentFunction}${label}"
        return f"{self.currentFile}${label}"

    def writeFunction(self, functionName: str, nArgs: int) -> None:
        self.currentFunction = functionName
        self.write([f"({functionName})"])
        for _ in range(nArgs):
            self.writePushPop(CommandType.C_PUSH, "constant", 0)

    def writeCall(self, functionName: str, nArgs: int) -> None:
        retLabel = self._returnAddrLabel(functionName)
        self.write([f"@{retLabel}", "D=A"] + PUSH_ASM)
        self.write(["@LCL", "D=M"] + PUSH_ASM)
        self.write(["@ARG", "D=M"] + PUSH_ASM)
        self.write(["@THIS", "D=M"] + PUSH_ASM)
        self.write(["@THAT", "D=M"] + PUSH_ASM)
        # ARG = SP-5-nArgs
        self.write(["@SP", "D=M", "@5", "D=D-A", f"@{nArgs}", "D=D-A", "@ARG", "M=D"])
        # LCL = SP
        self.write(["@SP", "D=M", "@LCL", "M=D"])
        # goto f
        self.write([f"@{functionName}", "0;JMP"])
        # f label
        self.write([f"({retLabel})"])

    def writeReturn(self) -> None:
        # use R13 for frame, R14 for retAddr
        # frame = LCL
        self.write(["@LCL", "D=M", "@R13", "M=D"])
        # retAddr = *(frame-5)
        self.write(["@R13", "D=M", "@5", "D=D-A", "A=D", "D=M", "@R14", "M=D"])
        # *ARG = pop()
        self.write(POP_ASM + ["@ARG", "A=M", "M=D"])
        # SP = ARG+1
        self.write(["@ARG", "D=M+1", "@SP", "M=D"])
        # restore that/this/arg/lcl
        for l in ["THAT", "THIS", "ARG", "LCL"]:
            self.write(["@R13", "AM=M-1", "D=M", f"@{l}", "M=D"])
        # goto retAddr
        self.write(["@R14", "A=M", "0;JMP"])

    def _returnAddrLabel(self, functionName: str) -> str:
        label = f"{functionName}$ret.{self.return_counter}"
        self.return_counter += 1
        return label

    def write(self, asms: list[str]) -> None:
        for a in asms:
            self.file.write(a + "\n")

    def setFileName(self, fileName: str) -> None:
        self.currentFile, _ = os.path.splitext(fileName)
        self.currentFunction = None

    def close(self):
        if hasattr(self, "file") and not self.file.closed:
            self.write(["(END)", "@END", "0;JMP"])
            self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
