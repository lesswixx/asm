from __future__ import annotations

import argparse
import re
import typing

from isa import (
    Arg,
    ArgType,
    Code,
    DataSection,
    Opcode,
    Term,
    TextSection,
    command_args,
    opcode_by_str,
    reg_by_str,
    serialize,
)


def read_source(src: typing.TextIO) -> str:
    return src.read()


section_pattern = re.compile(r"section \.(\w+)")
label_pattern = re.compile(r"(\w+):")
local_label_pattern = re.compile(r".(\w+):")

string_pattern = re.compile(r"\"(.*?)\"")


def int_to_bytes(i: int, size: int) -> bytearray:
    assert i >= 0, f"must be non negative, got {i}"
    assert i < (1 << (8 * size)), f"value would lose precision, got {i} with size {size}"
    binary = []
    while size > 0:
        binary.append(i & 0xFF)
        i >>= 8
        size -= 1
    binary = binary[::-1]
    return bytearray(binary)


def extract_data_section(lines: list[str]) -> (int, DataSection):
    match = section_pattern.fullmatch(lines[0])
    assert match is not None, f'Unknown line outside of section "{lines[0]}"'
    sect_name = match.groups()[0]
    if sect_name != "data":
        return 0, DataSection({})
    data = {}
    for i, line in enumerate(lines[1:]):
        match = section_pattern.fullmatch(line)
        if match:
            return i + 1, DataSection(data)
        match = label_pattern.match(line)
        assert match is not None, f'Each constant must start with label, got "{line}"'
        label = match.groups()[0]
        label_val = line[match.end(0) :].strip()
        match = string_pattern.match(label_val)
        assert match is not None, f'Unknown label val, got "{label_val}"'
        str_val = match.groups()[0].encode("raw_unicode_escape").decode("unicode_escape")
        data[label] = str_val
    return len(lines), DataSection(data)


register_pattern = re.compile(r"((r[0-4])|(a[0-4])|(sp))")
number_pattern = re.compile(r"(-?[0-9]+)")
address_exact_pattern = re.compile(r"\*" + number_pattern.pattern)
address_register_pattern = re.compile(r"\*" + register_pattern.pattern)
label_arg_pattern = re.compile(r"\w+")
local_label_arg_pattern = re.compile(r"\.?(\w+)")


def parse_arg(arg: str) -> Arg:
    match = address_exact_pattern.fullmatch(arg)
    if match:
        return Arg(ArgType.ADDRESS_EXACT, val=int(match.groups()[0]))
    match = address_register_pattern.fullmatch(arg)
    if match:
        reg = reg_by_str[match.groups()[0]]
        return Arg(ArgType.ADDRESS_REGISTER, reg=reg)
    match = number_pattern.fullmatch(arg)
    if match:
        return Arg(ArgType.NUMBER, val=int(arg))
    match = register_pattern.fullmatch(arg)
    if match:
        reg = reg_by_str[arg]
        return Arg(ArgType.REGISTER, reg=reg)
    match = label_arg_pattern.fullmatch(arg)
    if match:
        return Arg(ArgType.LABEL, symbol=arg)
    match = local_label_arg_pattern.fullmatch(arg)
    if match:
        return Arg(ArgType.LOCAL_LABEL, symbol=match.groups()[0])
    raise NotImplementedError(f'Unknown argument, got "{arg}"')


opts: dict[str, list[Opcode]] = {"mov": [Opcode.MOVE_NUM_TO_REG, Opcode.MOVE_MEMR_TO_REG, Opcode.MOVE_MEMR_TO_MEMX]}


def replace_special(cmd: str, args: list[Arg]) -> str:
    if cmd not in opts:
        return cmd
    options = opts[cmd]
    for option in options:
        valid_args = command_args[option]
        if len(valid_args) != len(args):
            continue
        match = True
        for i in range(len(args)):
            if args[i].tag not in valid_args[i]:
                match = False
                break
        if not match:
            continue
        return option
    raise NotImplementedError(f"Unexpected special command {cmd} with args {args}")


def parse_term(line: str, context: str) -> Term:
    space_idx = line.find(" ")
    command = line if space_idx == -1 else line[:space_idx]
    args = (
        []
        if space_idx == -1
        else list(map(lambda s: parse_arg(s), map(lambda s: s.strip(), line[space_idx + 1 :].split(","))))
    )
    for arg in args:
        if arg.tag == ArgType.LOCAL_LABEL:
            arg.symbol = f"{context}_{arg.symbol}"
            arg.tag = ArgType.LABEL
    command = replace_special(command, args)
    assert command in command_args, f'Unknown command "{command}"'
    valid_args = command_args[command]
    assert len(valid_args) == len(
        args
    ), f"Wrong amount of arguments for command {command}, has {len(valid_args)} but got {len(args)}"
    for j in range(len(args)):
        assert (
            args[j].tag in valid_args[j]
        ), f"Wrong type of argument for command {command}, can be {valid_args[j]} but got {args[j].tag}"
    return Term(opcode_by_str[command], args)


def extract_text_section(lines: list[str]) -> (int, TextSection):
    match = section_pattern.fullmatch(lines[0])
    assert match is not None, f'Unknown line outside of section "{lines[0]}"'
    sect_name = match.groups()[0]
    if sect_name != "text":
        return 0, TextSection([])
    context, label, local_label = None, None, None
    text = []
    for i, line in enumerate(lines[1:]):
        match = section_pattern.fullmatch(line)
        if match:
            return i + 1, TextSection(text)
        match = label_pattern.fullmatch(line)
        if match:
            context = label = match.groups()[0]
            continue
        match = local_label_pattern.fullmatch(line)
        if match:
            local_label = match.groups()[0]
            continue
        term = parse_term(line, context)
        if label:
            term.label = label
            label = None
        if local_label:
            term.label = f"{context}_{local_label}"
            local_label = None
        text.append(term)
    return len(lines), TextSection(text)


def translate(src: str) -> Code:
    lines: list[str] = list(
        filter(lambda s: s != "", map(lambda s: s.strip(), map(lambda s: s.split(";")[0], src.split("\n"))))
    )
    index, data_section = extract_data_section(lines)
    lines = lines[index:]
    index, text_section = extract_text_section(lines)
    assert index == len(lines), f'Unknown lines starting from "{lines[0]}"'
    return Code(data_section, text_section)


def write_code(dst: typing.TextIO, code: Code):
    dst.write(serialize(code))


def main(src: typing.TextIO, dst: typing.TextIO):
    source = read_source(src)
    code = translate(source)
    write_code(dst, code)

    loc, code_instr = len(source.split("\n")), len(code)
    print(f"LoC: {loc} code instr: {code_instr}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translates code into en executable file.")
    parser.add_argument(
        "src", type=argparse.FileType(encoding="utf-8"), metavar="source_file", help="file with source code"
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="dst",
        type=argparse.FileType("w"),
        default="output",
        metavar="output_file",
        help="file for storing an executable (default: output)",
    )
    namespace = parser.parse_args()
    main(namespace.src, namespace.dst)
