from __future__ import annotations

import argparse
import re
import typing

from isa import Arg, ArgType, Opcode, Term


def read_source(src: typing.TextIO) -> str:
    return src.read()


section_pattern = re.compile(r"section \.(\w+)")
label_pattern = re.compile(r"(\w+):")
local_label_pattern = re.compile(r".(\w+):")

string_pattern = re.compile(r"\"(.*?)\"")


class DataSection:
    def __init__(self, data: dict[str, bytearray]):
        self.data = data


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
        binary = bytearray()
        for symbol in str_val:
            binary.extend(int_to_bytes(ord(symbol), 4))
        data[label] = binary
    return len(lines), DataSection(data)


def parse_mov_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.MOVE)


def parse_inc_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.INCREMENT)


def parse_dec_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.DECREMENT)


def parse_cmp_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.COMPARE)


def parse_je_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.JUMP_EQUAL)


def parse_jmp_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.JUMP)


def parse_call_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.CALL)


def parse_ret_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.RETURN)


def parse_halt_command(args: list[str], ctx: str) -> Term:
    return Term(Opcode.HALT)


command_handlers: dict[str, typing.Callable[[list[str], str], Term]] = {
    "mov": parse_mov_command,
    "inc": parse_inc_command,
    "dec": parse_dec_command,
    "cmp": parse_cmp_command,
    "je": parse_je_command,
    "jmp": parse_jmp_command,
    "call": parse_call_command,
    "ret": parse_ret_command,
    "halt": parse_halt_command,
}


class TextSection:
    def __init__(self, terms: list[Term]):
        assert len(terms) > 0, "Text section cannot be empty"
        if terms[0].label != "start":
            terms.insert(0, Term(Opcode.JUMP, [Arg(ArgType.LABEL, symbol="start")]))
        self.terms = terms


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
        space_idx = line.find(" ")
        command = line if space_idx == -1 else line[:space_idx]
        assert command in command_handlers, f'Unknown command "{command}"'
        handler = command_handlers[command]
        args = list(map(lambda s: s.strip(), line[space_idx + 1 :].split(",")))
        term = handler(args, context)
        if label:
            term.label = label
            label = None
        if local_label:
            term.label = f"{context}_{local_label}"
            local_label = None
        text.append(term)
    return len(lines), TextSection(text)


class Code:
    def __init__(self, data: DataSection, text: TextSection):
        self.data = data
        self.text = text


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
    pass


def main(src: typing.TextIO, dst: typing.TextIO):
    source = read_source(src)
    code = translate(source)
    write_code(dst, code)


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
