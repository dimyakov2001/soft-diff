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
MAX_INDEX_SYMBOLS = 0


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
        equal_string = "  -  "
    elif equal_idxs[0] == 0:
        equal_string = "  +  "
    else:
        equal_string = "  o  "

    index_str_len = len(str(line_idx)) + 2
    max_line_len = (TERMINAL_COLUMNS - MAX_INDEX_SYMBOLS - index_str_len - len(equal_string)) // 2

    line1 = f"{line1} ({equal_idxs[1]})" if equal_idxs[0] > 0 else line1

    zip_lines = zip_longest(
        textwrap.wrap(line1, max_line_len),
        textwrap.wrap(line2, max_line_len),
        fillvalue=""
    )

    for i, (l1, l2) in enumerate(zip_lines):
        idx_str = f"{line_idx}) " if i == 0 else " "
        print(
            idx_str + " " * (MAX_INDEX_SYMBOLS - len(idx_str)),
            l1,
            " " * (max_line_len - len(l1)),
            equal_string if i == 0 else "     ",
            l2,
            sep=""
        )


def main() -> None:
    global MAX_INDEX_SYMBOLS
    args = parse_args()

    file1 = read_file(args.file1)
    file2 = read_file(args.file2)

    MAX_INDEX_SYMBOLS = len(str(max(file1.lines_count, file2.lines_count))) + 2

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

        equal_idxs = compare_lines(file1_p, file2_p, i)
        print_lines(i, line1, line2, equal_idxs)


if __name__ == "__main__":
    main()
