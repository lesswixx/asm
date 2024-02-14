from __future__ import annotations

import argparse
import copy
import logging
import typing
from enum import Enum

from isa import Arg, ArgType, Opcode, Reg, Word, WordTag, deserialize


def read_code(src: typing.TextIO) -> list[Word]:
    text = src.read()
    return deserialize(text)


def read_input(in_file: typing.TextIO) -> list[str]:
    if in_file is None:
        return []
    tokens = []
    for char in in_file.read():
        tokens.append(char)
    return tokens


INPUT_ADDRESS = 1000
OUTPUT_ADDRESS = 1001


class AluOp(Enum):
    SUM = "+"
    SUB = "-"
    MOD = "%"


def extend_bits(val: int, count: int) -> int:
    bit = (val >> (count - 1)) & 0x1
    if bit == 0:
        return val & ((1 << count) - 1)
    return val | ((-1) << count)


mask_32 = (1 << 32) - 1


n_flag = 0x8
z_flag = 0x4
v_flag = 0x2
c_flag = 0x1


def alu_sum(left: int, right: int) -> (int, int):
    result, carry = 0, 0
    for i in range(64):
        bit_res = ((left >> i) & 0x1) + ((right >> i) & 0x1) + ((carry >> i) & 0x1)
        result |= (bit_res & 0x1) << i
        carry |= (bit_res & 0x2) << i
    flags = 0
    if (result >> 63) & 0x1 == 1:
        flags |= n_flag
    if result & mask_32 == 0:
        flags |= z_flag
    if ((carry >> 63) & 0x1) != ((carry >> 64) & 0x1):
        flags |= v_flag
    if (carry >> 64) & 0x1 == 1:
        flags |= c_flag
    return result & mask_32, flags


class DataPath:
    def __init__(self, memory_size: int, program: list[Word], input_tokens: list[str]):
        assert memory_size >= len(program), "data_memory_size must be greater than data_memory size"
        for word in program:
            if word.tag == WordTag.BINARY:
                assert 0 <= word.val < (1 << 32), "all binary words in memory must be uint32"
        self.memory_size = memory_size
        self.memory = copy.deepcopy(program)
        for _ in range(memory_size - len(program)):
            self.memory.append(Word(WordTag.BINARY, val=0))
        self.input_tokens = input_tokens
        self.output_tokens = []
        # registers
        self.ir = None
        self.a0, self.a1, self.a2, self.a3 = 0, 0, 0, 0
        self.r0, self.r1, self.r2, self.r3 = 0, 0, 0, 0
        self.ar, self.dr, self.ip, self.sp = 0, 0, 0, memory_size
        self.fl = 0

    def signal_read_memory(self):
        assert self.ar < self.memory_size, f"ar ({self.ar}) out of memory_size ({self.memory_size})"
        if self.ar == INPUT_ADDRESS:
            if len(self.input_tokens) == 0:
                raise EOFError()
            symbol = self.input_tokens.pop(0)
            logging.debug(f"input: {symbol!r} <- {''.join(self.input_tokens)!r}")
            self.dr = ord(symbol)
        else:
            word = self.memory[self.ar]
            assert word.tag == WordTag.BINARY, f"unknown word tag to read {word.tag}"
            self.dr = word.val

    def signal_write_memory(self):
        if self.ar == OUTPUT_ADDRESS:
            assert 0 <= self.dr <= 0x10FFFF, f"dar contains unknown symbol, got {self.dr}"
            symbol = chr(self.dr)
            logging.debug(f"output: {''.join(self.output_tokens)!r} <- {symbol!r}")
            self.output_tokens.append(symbol)
        else:
            word = self.memory[self.ar]
            assert word.tag == WordTag.BINARY, f"Cant write in read-only memory {word.tag}"
            word.val = self.dr

    def negative(self) -> bool:
        return self.fl & n_flag != 0

    def zero(self) -> bool:
        return self.fl & z_flag != 0

    def overflow(self) -> bool:
        return self.fl & v_flag != 0

    def carry(self) -> bool:
        return self.fl & c_flag != 0

    def get_reg_val(self, reg: Reg | None) -> int:
        if reg is None:
            return 0
        return getattr(self, reg)

    def alu(self, left: int, right: int, op: AluOp, set_flags: bool) -> int:
        if op == AluOp.SUM:
            output, flags = alu_sum(left & mask_32, right & mask_32)
            if set_flags:
                self.fl = flags
        elif op == AluOp.SUB:
            output = left - right
        elif op == AluOp.MOD:
            assert left >= 0, f"mod can performed only with non-negatives, got left={left}"
            assert right > 0, f"mod can performed only with positive argument, got right={right}"
            output = left % right
        else:
            raise NotImplementedError(op)
        return output & mask_32

    def set_regs_from_alu(self, alu_out: int, regs: list[Reg]):
        for reg in regs:
            setattr(self, reg, alu_out)

    def signal_alu(
        self,
        left: int = 0,
        right: int = 0,
        alu_op: AluOp = AluOp.SUM,
        set_regs: list[Reg] | None = None,
        set_flags: bool = False,
    ):
        if set_regs is None:
            set_regs = []
        left_val = extend_bits(left, 32)
        right_val = extend_bits(right, 32)
        output = self.alu(left_val, right_val, alu_op, set_flags)
        self.set_regs_from_alu(output, set_regs)

    def signal_fetch_opcode(self) -> Opcode:
        self.ir = self.memory[self.ip]
        assert self.ir.tag == WordTag.OPCODE, f"Cant fetch opcode, next is {self.ir.tag}"
        return self.ir.op

    def signal_fetch_arg(self) -> Arg:
        self.ir = self.memory[self.ip]
        assert self.ir.tag == WordTag.ARGUMENT, f"Cant fetch argument, next is {self.ir.tag}"
        return self.ir.arg

    def __repr__(self):
        regs_repr = (
            f"ip={hex(self.ip)}\tar={hex(self.ar)}\tdr={hex(self.dr)}\t"
            f"a0={hex(self.a0)}\ta1={hex(self.a1)}\ta2={hex(self.a2)}\ta3={hex(self.a3)}\t"
            f"r0={hex(self.r0)}\tr1={hex(self.r1)}\tr2={hex(self.r2)}\tr3={hex(self.r3)}\t"
            f"sp={hex(self.sp)}\tfl={hex(self.fl)}"
        )
        stack_repr = f"stack_top={'?' if self.sp >= self.memory_size else hex(self.memory[self.sp].val)}"
        return f"{regs_repr}\t{stack_repr}".expandtabs(10)


class ControlUnit:
    def __init__(self, data_path: DataPath):
        self.dp = data_path
        self.ticks = 0

        self.control_instruction_executors: dict[Opcode, typing.Callable[[], None]] = {
            Opcode.HALT: self.execute_halt_control_instruction,
            Opcode.CALL: self.execute_call_control_instruction,
            Opcode.RETURN: self.execute_return_control_instruction,
            Opcode.JUMP_EQUAL: self.execute_jump_equal_control_instruction,
            Opcode.JUMP: self.execute_jump_control_instruction,
        }

        self.ordinary_instruction_executors: dict[Opcode, typing.Callable[[], None]] = {
            Opcode.MOVE_NUM_TO_REG: self.execute_move_num_to_reg_instruction,
            Opcode.MOVE_MEMR_TO_REG: self.execute_move_memr_to_reg_instruction,
            Opcode.MOVE_MEMR_TO_MEMX: self.execute_move_memr_to_memx_instruction,
            Opcode.MOVE_MEMX_TO_MEMX: self.execute_move_memx_to_memx_instruction,
            Opcode.INCREMENT: self.execute_increment_instruction,
            Opcode.DECREMENT: self.execute_decrement_instruction,
            Opcode.COMPARE: self.execute_compare_instruction,
        }

    def tick(self):
        self.ticks += 1

    def fetch_opcode(self) -> Opcode:
        op = self.dp.signal_fetch_opcode()
        self.tick()
        return op

    def fetch_arg(self) -> Arg:
        self.dp.signal_alu(left=self.dp.ip, right=1, set_regs=[Reg.IP])
        self.tick()
        arg = self.dp.signal_fetch_arg()
        self.tick()
        return arg

    def execute_halt_control_instruction(self):
        raise StopIteration()

    def execute_call_control_instruction(self):
        arg = self.fetch_arg()
        assert arg.tag == ArgType.NUMBER, f"Wrong argument of call, got {arg}"
        self.dp.signal_alu(left=self.dp.sp, right=1, alu_op=AluOp.SUB, set_regs=[Reg.SP, Reg.AR])
        self.tick()
        self.dp.signal_alu(left=self.dp.ip, right=1, set_regs=[Reg.DR])
        self.tick()
        self.dp.signal_write_memory()
        self.tick()
        self.dp.signal_alu(left=arg.val, set_regs=[Reg.IP])
        self.tick()

    def execute_return_control_instruction(self):
        self.dp.signal_alu(left=self.dp.sp, set_regs=[Reg.AR])
        self.tick()
        self.dp.signal_read_memory()
        self.tick()
        self.dp.signal_alu(left=self.dp.dr, set_regs=[Reg.IP])
        self.tick()
        self.dp.signal_alu(left=self.dp.sp, right=1, set_regs=[Reg.SP])
        self.tick()

    def execute_jump_equal_control_instruction(self):
        arg = self.fetch_arg()
        assert arg.tag == ArgType.NUMBER, f"Wrong argument of je, got {arg}"
        if self.dp.zero():
            self.dp.signal_alu(left=arg.val, set_regs=[Reg.IP])
            self.tick()
        else:
            self.dp.signal_alu(left=self.dp.ip, right=1, set_regs=[Reg.IP])
            self.tick()

    def execute_jump_control_instruction(self):
        arg = self.fetch_arg()
        assert arg.tag == ArgType.NUMBER, f"Wrong argument of jmp, got {arg}"
        self.dp.signal_alu(left=arg.val, set_regs=[Reg.IP])
        self.tick()

    def execute_control_instruction(self, op: Opcode) -> bool:
        if op not in self.control_instruction_executors:
            return False
        self.control_instruction_executors[op]()
        return True

    def execute_move_num_to_reg_instruction(self):
        num = self.fetch_arg()
        assert num.tag == ArgType.NUMBER, f"Wrong argument of movnmtrg, got {num}"
        reg = self.fetch_arg()
        assert reg.tag == ArgType.REGISTER, f"Wrong argument of movnmtrg, got {reg}"
        self.dp.signal_alu(left=num.val, set_regs=[reg.reg])
        self.tick()

    def execute_move_memr_to_reg_instruction(self):
        memr = self.fetch_arg()
        assert memr.tag == ArgType.ADDRESS_REGISTER, f"Wrong argument of movmrtrg, got {memr}"
        self.dp.signal_alu(left=self.dp.get_reg_val(memr.reg), set_regs=[Reg.AR])
        self.tick()
        self.dp.signal_read_memory()
        self.tick()
        reg = self.fetch_arg()
        assert reg.tag == ArgType.REGISTER, f"Wrong argument of movmrtrg, got {reg}"
        self.dp.signal_alu(left=self.dp.dr, set_regs=[reg.reg])
        self.tick()

    def execute_move_memr_to_memx_instruction(self):
        memr = self.fetch_arg()
        assert memr.tag == ArgType.ADDRESS_REGISTER, f"Wrong argument of movmrtmx, got {memr}"
        self.dp.signal_alu(left=self.dp.get_reg_val(memr.reg), set_regs=[Reg.AR])
        self.tick()
        self.dp.signal_read_memory()
        self.tick()
        memx = self.fetch_arg()
        assert memx.tag == ArgType.ADDRESS_EXACT, f"Wrong argument of movmrtmx, got {memx}"
        self.dp.signal_alu(left=memx.val, set_regs=[Reg.AR])
        self.tick()
        self.dp.signal_write_memory()
        self.tick()

    def execute_move_memx_to_memx_instruction(self):
        memx = self.fetch_arg()
        assert memx.tag == ArgType.ADDRESS_EXACT, f"Wrong argument of movmxtmx, got {memx}"
        self.dp.signal_alu(left=memx.val, set_regs=[Reg.AR])
        self.tick()
        self.dp.signal_read_memory()
        self.tick()
        memx = self.fetch_arg()
        assert memx.tag == ArgType.ADDRESS_EXACT, f"Wrong argument of movmxtmx, got {memx}"
        self.dp.signal_alu(left=memx.val, set_regs=[Reg.AR])
        self.tick()
        self.dp.signal_write_memory()
        self.tick()

    def execute_increment_instruction(self):
        reg = self.fetch_arg()
        assert reg.tag == ArgType.REGISTER, f"Wrong argument of inc, got {reg}"
        self.dp.signal_alu(left=self.dp.get_reg_val(reg.reg), right=1, set_regs=[reg.reg])
        self.tick()

    def execute_decrement_instruction(self):
        reg = self.fetch_arg()
        assert reg.tag == ArgType.REGISTER, f"Wrong argument of dec, got {reg}"
        self.dp.signal_alu(left=self.dp.get_reg_val(reg.reg), right=1, alu_op=AluOp.SUB, set_regs=[reg.reg])
        self.tick()

    def execute_compare_instruction(self):
        reg = self.fetch_arg()
        assert reg.tag == ArgType.REGISTER, f"Wrong argument of cmp, got {reg}"
        num = self.fetch_arg()
        assert num.tag == ArgType.NUMBER, f"Wrong argument of cmp, got {num}"
        self.dp.signal_alu(left=self.dp.get_reg_val(reg.reg), right=num.val, set_flags=True)
        self.tick()

    def execute_ordinary_instruction(self, op: Opcode):
        assert op in self.ordinary_instruction_executors, f"Unknown instruction, got {op}"
        self.ordinary_instruction_executors[op]()
        self.dp.signal_alu(left=self.dp.ip, right=1, set_regs=[Reg.IP])
        self.tick()

    def execute_next_instruction(self):
        op = self.dp.signal_fetch_opcode()
        logging.debug(f"{op.name}\t{self}".expandtabs(20))
        if not self.execute_control_instruction(op):
            self.execute_ordinary_instruction(op)

    def __repr__(self):
        state_repr = f"tick={self.ticks}"
        dp_repr = f"{self.dp}"
        return f"{state_repr}\t{dp_repr}".expandtabs(10)


def simulation(code: list[Word], input_tokens: list[str], data_memory_size: int = 0x800, limit: int = 1_000):
    data_path = DataPath(data_memory_size, code, input_tokens)
    control_unit = ControlUnit(data_path)
    instruction_proceed = 0

    try:
        while instruction_proceed < limit:
            control_unit.execute_next_instruction()
            instruction_proceed += 1
    except EOFError:
        logging.warning("Input buffer is empty")
    except StopIteration:
        pass

    if instruction_proceed >= limit:
        logging.warning(f"Limit {limit} exceeded")

    return "".join(data_path.output_tokens), instruction_proceed, control_unit.ticks


def main(src: typing.TextIO, in_file: typing.TextIO):
    logging.getLogger().setLevel(logging.DEBUG)

    code = read_code(src)
    input_tokens = read_input(in_file)
    output, instr, ticks = simulation(code, input_tokens)

    logging.info(f"instr: {instr} ticks: {ticks}")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute asm executable file.")
    parser.add_argument("src", type=argparse.FileType("r"), metavar="executable_file", help="executable file")
    parser.add_argument(
        "--input",
        "-i",
        dest="in_file",
        type=argparse.FileType(encoding="utf-8"),
        metavar="input_file",
        help="file with input data for executable (default: empty file)",
    )
    namespace = parser.parse_args()
    main(namespace.src, namespace.in_file)
