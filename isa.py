from __future__ import annotations

import json
from enum import Enum


class Reg(str, Enum):
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


reg_by_str: dict[str, Reg] = {r: r for r in Reg}


class ArgType(str, Enum):
    LABEL = "LABEL"
    LOCAL_LABEL = "LOCAL_LABEL"
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
            case ArgType.LABEL | ArgType.LOCAL_LABEL:
                s = self.symbol
            case ArgType.ADDRESS_EXACT:
                s = f"*{self.val}"
            case ArgType.ADDRESS_REGISTER:
                s = f"*{self.reg}"
            case ArgType.REGISTER:
                s = f"{self.reg}"
            case ArgType.NUMBER:
                s = f"{self.val}"
            case _:
                raise NotImplementedError(f'Unknown arg type "{self.tag}"')
        return s


class Opcode(str, Enum):
    MOVE_NUM_TO_REG = "movnmtrg"
    MOVE_MEMR_TO_REG = "movmrtrg"
    MOVE_MEMR_TO_MEMX = "movmrtmx"
    INCREMENT = "inc"
    DECREMENT = "dec"
    COMPARE = "cmp"
    JUMP_EQUAL = "je"
    JUMP = "jmp"
    CALL = "call"
    RETURN = "ret"
    HALT = "halt"


opcode_by_str: dict[str, Opcode] = {op: op for op in Opcode}


command_args: dict[str, list[list[ArgType]]] = {
    Opcode.MOVE_NUM_TO_REG: [[ArgType.REGISTER], [ArgType.NUMBER, ArgType.LABEL]],
    Opcode.MOVE_MEMR_TO_REG: [[ArgType.REGISTER], [ArgType.ADDRESS_REGISTER]],
    Opcode.MOVE_MEMR_TO_MEMX: [[ArgType.ADDRESS_EXACT], [ArgType.ADDRESS_REGISTER]],
    Opcode.INCREMENT: [[ArgType.REGISTER]],
    Opcode.DECREMENT: [[ArgType.REGISTER]],
    Opcode.COMPARE: [[ArgType.REGISTER], [ArgType.NUMBER]],
    Opcode.JUMP_EQUAL: [[ArgType.LABEL]],
    Opcode.JUMP: [[ArgType.LABEL]],
    Opcode.CALL: [[ArgType.LABEL]],
    Opcode.RETURN: [],
    Opcode.HALT: [],
}


class Term:
    def __init__(self, op: Opcode, args: list[Arg] | None = None, label: str | None = None):
        self.op = op
        self.args = [] if args is None else args
        self.label = label

    def __repr__(self):
        s = f"{self.op}"
        if self.args:
            s += " " + ", ".join(map(lambda a: repr(a), self.args))
        if self.label:
            s = f"{self.label}:\n" + s
        return s


class DataSection:
    def __init__(self, data: dict[str, bytearray]):
        self.data = data


class TextSection:
    def __init__(self, terms: list[Term]):
        assert len(terms) > 0, "Text section cannot be empty"
        if terms[0].label != "start":
            terms.insert(0, Term(Opcode.JUMP, [Arg(ArgType.LABEL, symbol="start")]))
        self.terms = terms


class Code:
    def __init__(self, data: DataSection, text: TextSection):
        self.data = data
        self.text = text


def default_serialize(obj):
    if isinstance(obj, bytearray):
        return obj.hex(" ")
    return {k: v for k, v in obj.__dict__.items() if v is not None}


def serialize(code: Code) -> str:
    return json.dumps(code, default=default_serialize, indent=2)


def deserialize(string: str) -> Code:
    return json.loads(string)
