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
    IP = "ip"
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
    REGISTER_OP_NUMBER = "REGISTER_OP_NUMBER"
    OPERATION = "OPERATION"
    NUMBER = "NUMBER"


class Arg:
    def __init__(
        self,
        tag: ArgType,
        symbol: str | None = None,
        val: int | None = None,
        reg: Reg | None = None,
        op: str | None = None,
    ):
        self.tag = tag
        self.symbol = symbol
        self.val = val
        self.reg = reg
        self.op = op

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
            case ArgType.REGISTER_OP_NUMBER:
                s = f"{self.reg}{self.op}{self.val}"
            case ArgType.OPERATION:
                s = f"{self.op}"
            case ArgType.NUMBER:
                s = f"{self.val}"
            case _:
                raise NotImplementedError(f'Unknown arg type "{self.tag}"')
        return s


class Opcode(str, Enum):
    MOVE_NUM_TO_REG = "movnum2reg"
    MOVE_NUM_TO_MEM = "movnum2mem"
    MOVE_REG_TO_REG = "movreg2reg"
    MOVE_REG_TO_MEM = "movreg2mem"
    MOVE_MEM_TO_REG = "movmem2reg"
    MOVE_MEM_TO_MEM = "movmem2mem"
    MOVE_REG_OP_NUM_TO_REG = "movregnum2reg"
    INCREMENT = "inc"
    DECREMENT = "dec"
    ADD = "add"
    ADD_REG = "addreg"
    SUBTRACT = "sub"
    DIVIDE = "div"
    MODULO = "mod"
    COMPARE = "cmp"
    PUSH = "push"
    POP = "pop"
    JUMP_EQUAL = "je"
    JUMP_NOT_EQUAL = "jne"
    JUMP = "jmp"
    CALL = "call"
    RETURN = "ret"
    HALT = "halt"


opcode_by_str: dict[str, Opcode] = {op: op for op in Opcode}


REG_TYPE = [ArgType.REGISTER]
NUMBER_TYPE = [ArgType.NUMBER, ArgType.LABEL]


command_args: dict[str, tuple[int, list[list[ArgType]]]] = {
    Opcode.MOVE_NUM_TO_REG: [(1, [ArgType.REGISTER]), (0, [ArgType.NUMBER, ArgType.LABEL])],
    Opcode.MOVE_NUM_TO_MEM: [
        (1, [ArgType.ADDRESS_REGISTER, ArgType.ADDRESS_EXACT]),
        (0, [ArgType.NUMBER, ArgType.LABEL]),
    ],
    Opcode.MOVE_REG_TO_REG: [(1, [ArgType.REGISTER]), (0, [ArgType.REGISTER])],
    Opcode.MOVE_REG_TO_MEM: [(1, [ArgType.ADDRESS_REGISTER, ArgType.ADDRESS_EXACT]), (0, [ArgType.REGISTER])],
    Opcode.MOVE_MEM_TO_REG: [(1, [ArgType.REGISTER]), (0, [ArgType.ADDRESS_REGISTER, ArgType.ADDRESS_EXACT])],
    Opcode.MOVE_MEM_TO_MEM: [
        (1, [ArgType.ADDRESS_REGISTER, ArgType.ADDRESS_EXACT]),
        (0, [ArgType.ADDRESS_REGISTER, ArgType.ADDRESS_EXACT]),
    ],
    Opcode.MOVE_REG_OP_NUM_TO_REG: [(1, [ArgType.REGISTER]), (0, [ArgType.REGISTER_OP_NUMBER])],
    Opcode.INCREMENT: [(0, [ArgType.REGISTER])],
    Opcode.DECREMENT: [(0, [ArgType.REGISTER])],
    Opcode.ADD: [(0, [ArgType.REGISTER]), (1, [ArgType.NUMBER])],
    Opcode.ADD_REG: [(0, [ArgType.REGISTER]), (1, [ArgType.REGISTER])],
    Opcode.SUBTRACT: [(0, [ArgType.REGISTER]), (1, [ArgType.NUMBER])],
    Opcode.DIVIDE: [(0, [ArgType.REGISTER]), (1, [ArgType.NUMBER])],
    Opcode.MODULO: [(0, [ArgType.REGISTER]), (1, [ArgType.NUMBER])],
    Opcode.COMPARE: [(0, [ArgType.REGISTER]), (1, [ArgType.NUMBER])],
    Opcode.PUSH: [(0, [ArgType.REGISTER])],
    Opcode.POP: [(0, [ArgType.REGISTER])],
    Opcode.JUMP_EQUAL: [(0, [ArgType.LABEL])],
    Opcode.JUMP_NOT_EQUAL: [(0, [ArgType.LABEL])],
    Opcode.JUMP: [(0, [ArgType.LABEL])],
    Opcode.CALL: [(0, [ArgType.LABEL])],
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
    def __init__(self, data: dict[str, str]):
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

    def __len__(self):
        return len(self.text.terms)


class WordTag(str, Enum):
    OPCODE = "OPCODE"
    ARGUMENT = "ARGUMENT"
    BINARY = "BINARY"


class Word:
    def __init__(self, tag: WordTag, op: Opcode | None = None, arg: Arg | None = None, val: int | None = None):
        self.tag = tag
        self.op = op
        self.arg = arg
        self.val = val

    def __repr__(self):
        s = f"{self.tag}"
        if self.op:
            s += f" {self.op}"
        if self.arg:
            s += f" {self.arg}"
        if self.val:
            s += f" {self.val}"
        return s


def ordered_args(term: Term) -> list[Arg]:
    ord_args = command_args[term.op]
    args = []
    for i in range(len(term.args)):
        for j, ord_arg in enumerate(ord_args):
            if ord_arg[0] == i:
                args.append(term.args[j])
                break
    assert len(args) == len(ord_args), "Wrong usage of command_args"
    split_args = []
    for arg in args:
        if arg.tag == ArgType.REGISTER_OP_NUMBER:
            split_args.extend(
                [
                    Arg(ArgType.REGISTER, reg=arg.reg),
                    Arg(ArgType.OPERATION, op=arg.op),
                    Arg(ArgType.NUMBER, val=arg.val),
                ]
            )
        else:
            split_args.append(arg)
    return split_args


def term_to_words(term: Term) -> list[Word]:
    words = [Word(WordTag.OPCODE, op=term.op)]
    for arg in ordered_args(term):
        words.append(Word(WordTag.ARGUMENT, arg=arg))
    return words


def data_to_words(data: str) -> list[Word]:
    words = [Word(WordTag.BINARY, val=len(data))]
    for char in data:
        words.append(Word(WordTag.BINARY, val=ord(char)))
    return words


def default_serialize(obj):
    return {k: v for k, v in obj.__dict__.items() if v is not None}


def serialize(code: Code) -> str:
    symbol_table = {}
    words = []
    for term in code.text.terms:
        if term.label:
            symbol_table[term.label] = len(words)
        words.extend(term_to_words(term))
    if len(code.data.data) > 0:
        words.append(Word(WordTag.BINARY, val=0))
    for symbol, data in code.data.data.items():
        symbol_table[symbol] = len(words)
        words.extend(data_to_words(data))
    for word in words:
        if word.tag == WordTag.ARGUMENT:
            arg = word.arg
            assert arg.tag != ArgType.LOCAL_LABEL, f"Found unresolved local label {arg}"
            if arg.tag == ArgType.LABEL:
                assert arg.symbol in symbol_table, f"Cant resolve label {arg.symbol}"
                arg.tag = ArgType.NUMBER
                arg.val = symbol_table[arg.symbol]
    return json.dumps(words, default=default_serialize, indent=2)


def deserialize_arg(raw_arg: dict) -> Arg:
    arg_type = ArgType(raw_arg["tag"])
    arg = Arg(arg_type)
    match arg_type:
        case ArgType.NUMBER | ArgType.ADDRESS_EXACT:
            arg.val = raw_arg["val"]
        case ArgType.REGISTER | ArgType.ADDRESS_REGISTER:
            arg.reg = raw_arg["reg"]
        case ArgType.OPERATION:
            arg.op = raw_arg["op"]
    return arg


def deserialize(string: str) -> list[Word]:
    words = []
    raw_words = json.loads(string)
    for raw_word in raw_words:
        tag = WordTag(raw_word["tag"])
        word = Word(tag)
        match tag:
            case WordTag.OPCODE:
                word.op = Opcode(raw_word["op"])
            case WordTag.ARGUMENT:
                word.arg = deserialize_arg(raw_word["arg"])
            case WordTag.BINARY:
                word.val = raw_word["val"]
        words.append(word)
    return words
