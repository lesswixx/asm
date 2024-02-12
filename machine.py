from __future__ import annotations

import argparse
import typing

from isa import Word, deserialize


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


def simulation(code: list[Word], input_tokens: list[str], data_memory_size: int = 0x1FFF, limit: int = 5_000):
    pass


def main(src: typing.TextIO, in_file: typing.TextIO):
    code = read_code(src)
    input_tokens = read_input(in_file)
    simulation(code, input_tokens)


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
