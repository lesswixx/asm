from __future__ import annotations

from enum import Enum


class Reg(tuple[str], Enum):
    R0 = "r0"
    R1 = "r1"
    R2 = "r2"
    R3 = "r3"
    A0 = "a0"
    A1 = "a1"
    A2 = "a2"
    A3 = "a3"
    SP = "sp"
    AR = "ar"
    DR = "dr"


class ArgType(tuple[str], Enum):
    LABEL = "LABEL"
    ADDRESS_EXACT = "ADDRESS_EXACT"
    ADDRESS_REGISTER = "ADDRESS_REGISTER"
    REGISTER = "REGISTER"
    NUMBER = "NUMBER"


class Arg:
    def __init__(self, tag: ArgType, symbol: str | None = None, val: int | None = None, reg: Reg | None = None):
        self.tag = tag
        self.symbol = symbol
        self.val = val
        self.reg = reg

    def __repr__(self):
        match self.tag:
            case ArgType.LABEL:
                s = self.symbol
            case ArgType.ADDRESS_EXACT:
                s = f"*{self.val}"
            case ArgType.ADDRESS_REGISTER:
                s = f"*{self.reg!r}"
            case ArgType.REGISTER:
                s = f"{self.reg!r}"
            case ArgType.NUMBER:
                s = f"{self.val}"
            case _:
                raise NotImplementedError(f'Unknown arg type "{self.tag}"')
        return s


class Opcode(tuple[str], Enum):
    MOVE = "mov"
    INCREMENT = "inc"
    DECREMENT = "dec"
    COMPARE = "cmp"
    JUMP_EQUAL = "je"
    JUMP = "jmp"
    CALL = "call"
    RETURN = "ret"
    HALT = "halt"


class Term:
    def __init__(self, op: Opcode, args: list[Arg] | None = None, label: str | None = None):
        self.op = op
        self.args = [] if args is None else args
        self.label = label

    def __repr__(self):
        s = f"{self.op.value[0]}"
        if self.args:
            s += " " + ", ".join(map(lambda a: repr(a), self.args))
        if self.label:
            s = f"{self.label}:\n" + s
        return s
