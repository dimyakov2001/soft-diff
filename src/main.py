import argparse
import shutil
import textwrap
from functools import partial
from itertools import zip_longest
from typing import List, Tuple
import re
from copy import copy

from pydantic import BaseModel

TERMINAL_COLUMNS = shutil.get_terminal_size().columns


class Args(BaseModel):
    file1: str
    file2: str
    ignore_tabs: bool
    ignore_tail_commas: bool

def parse_args() -> Args:
    parser = argparse.ArgumentParser()

    parser.add_argument("file1")
    parser.add_argument("file2")
    parser.add_argument("-t", "--ignore-tabs", action="store_true")
    parser.add_argument("-c", "--ignore-tail-commas", action="store_true")

    args = parser.parse_args()
    return Args.model_validate(dict(args._get_kwargs()))


class FileContent(BaseModel):
    lines: List[str]
    lines_count: int
    max_line_len: int


def read_file(filepath: str) -> FileContent:
    with open(filepath, "r") as file:
        lines = file.readlines()

        return FileContent(
            lines=lines,
            lines_count=len(lines),
            max_line_len=max(len(line) for line in lines)
        )

def preprocess_data(file: FileContent, strip: bool = False, remove_commas: bool = False) -> FileContent:
    lines = file.lines

    if strip:
        lines = [line.strip() for line in lines]
    
    if remove_commas:
        lines = [re.sub("[,:] *$", "", line) for line in lines]

    file_ = copy(file)
    file_.lines = lines
    return file_


def print_lines(line_idx: int, line1: str, line2: str, equal_idxs: Tuple[int, int]) -> None:
    if equal_idxs[0] == -1:
        equal_string = "-"
    elif equal_idxs[0] == 0:
        equal_string = "+"
    else:
        equal_string = f"({equal_idxs[0]}:{equal_idxs[1]})"
    equal_string = f"  {equal_string}  "

    index_str_len = len(str(line_idx)) + 2
    max_line_len = (TERMINAL_COLUMNS - index_str_len - len(equal_string)) // 2

    zip_lines = zip_longest(
        textwrap.wrap(line1, max_line_len),
        textwrap.wrap(line2, max_line_len),
        fillvalue=""
    )

    for i, (l1, l2) in enumerate(zip_lines):
        print(
            f"{line_idx}) " if i == 0 else " " * (len(str(line_idx)) + 2),
            l1,
            " " * (max_line_len - len(l1)),
            equal_string,
            l2,
            sep=""
        )


def main() -> None:
    args = parse_args()

    file1 = read_file(args.file1)
    file2 = read_file(args.file2)

    preprocess_data_ = partial(preprocess_data, strip=args.ignore_tabs, remove_commas=args.ignore_tail_commas)
    file1_p = preprocess_data_(file1)
    file2_p = preprocess_data_(file2)

    def get_file_line_by_idx(file: FileContent, line_idx: int) -> str:
        return file.lines[line_idx] if line_idx < file.lines_count else ""

    def compare_lines(file1: FileContent, file2: FileContent, line_idx: int) -> Tuple[int, int]:
        line1 = get_file_line_by_idx(file1, line_idx)
        line2 = get_file_line_by_idx(file2, line_idx)

        if line1 == line2:
            return (0, 0)

        for line2_idx, line2 in enumerate(file2.lines):
            if line1 == line2:
                return (line_idx, line2_idx)

        return (-1, -1)

    for i in range(max([file1.lines_count, file2.lines_count])):
        line1 = get_file_line_by_idx(file1, i)
        line2 = get_file_line_by_idx(file2, i)

        lines_are_equal = compare_lines(file1_p, file2_p, i)
        print_lines(i, line1, line2, lines_are_equal)


if __name__ == "__main__":
    main()
