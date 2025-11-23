import sys
import os
from parser import Parser, InstructionType
from hack_code import dest, comp, jump
from symbol import Symbol

RAM_START_ADDRESS = 16


def resolve_address(symbol: Symbol, sym: str, ram_addr: int) -> tuple[int, int]:
    if sym.isdigit():
        return int(sym), ram_addr

    if symbol.contains(sym):
        return symbol.getAddress(sym), ram_addr

    symbol.addEntry(sym, ram_addr)
    return ram_addr, ram_addr + 1


def generate_a_instruction(
    parser: Parser, symbol: Symbol, ram_addr: int
) -> tuple[str, int]:
    addr, new_ram_addr = resolve_address(symbol, parser.symbol(), ram_addr)
    return format(addr, "016b"), new_ram_addr


def main() -> None:
    if len(sys.argv) != 2:
        print("引数は一つのみ")
        sys.exit(1)

    asm_file = sys.argv[1]
    hack_file = asm_file.replace(".asm", ".hack")

    # 1 pass: ラベル処理
    symbol = Symbol()
    row_num = 0
    with Parser(asm_file) as p1:
        while p1.hasMoreLines():
            p1.advance()
            if p1.instructionType() == InstructionType.L_INSTRUCTION:
                symbol.addEntry(p1.symbol(), row_num)
            else:
                row_num += 1

    # 2 pass: コード生成
    ram_addr = RAM_START_ADDRESS
    try:
        with Parser(asm_file) as p2, open(hack_file, "w") as f:
            while p2.hasMoreLines():
                p2.advance()
                inst_type = p2.instructionType()

                if inst_type == InstructionType.A_INSTRUCTION:
                    bin_code, ram_addr = generate_a_instruction(p2, symbol, ram_addr)
                    f.write(bin_code + "\n")
                elif inst_type == InstructionType.C_INSTRUCTION:
                    bin_code = (
                        "111" + comp(p2.comp()) + dest(p2.dest()) + jump(p2.jump())
                    )
                    f.write(bin_code + "\n")
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(hack_file):
            os.remove(hack_file)
        sys.exit(1)


if __name__ == "__main__":
    main()
