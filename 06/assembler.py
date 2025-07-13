import sys
import os
from parser import Parser, InstructionType
from hack_code import dest, comp, jump


def main():
    if len(sys.argv) != 2:
        print("引数は一つのみ")
        sys.exit(1)

    asm_file = sys.argv[1]
    hack_file = asm_file.replace(".asm", ".hack")

    p = Parser(asm_file)
    try:
        with open(hack_file, "w") as f:
            while p.hasMoreLines():
                p.advance()
                instType = p.instructionType()

                if instType == InstructionType.A_INSTRUCTION:
                    # TODO: シンボルテーブル
                    bin_code = format(int(p.symbol()), "016b")
                elif instType == InstructionType.C_INSTRUCTION:
                    bin_code = "111" + comp(p.comp()) + dest(p.dest()) + jump(p.jump())
                else:
                    continue  # L_INSTRUCTION は出力しない

                f.write(bin_code + "\n")
        p.close()
    except Exception as e:
        print(f"Error: {e}")
        # エラー時は機械語ファイルを削除
        if os.path.exists(hack_file):
            os.remove(hack_file)
        sys.exit(1)


if __name__ == "__main__":
    main()
