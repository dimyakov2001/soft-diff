import argparse
import shutil
import textwrap
from functools import partial
from itertools import zip_longest
from typing import List

from pydantic import BaseModel

COLUMN_GAP = "  "
TERMINAL_COLUMNS = shutil.get_terminal_size().columns


class Args(BaseModel):
    file1: str
    file2: str
    ignore_tabs: bool

def parse_args() -> Args:
    parser = argparse.ArgumentParser()

    parser.add_argument("file1")
    parser.add_argument("file2")
    parser.add_argument("-t", "--ignore_tabs", action="store_true") 

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


def print_lines(line_idx: int, line1: str, line2: str, lines_are_equal: bool) -> None:
    index_str_len = len(str(line_idx)) + 2
    gap_str_len = 2 * len(COLUMN_GAP) + 1
    max_line_len = (TERMINAL_COLUMNS - index_str_len - gap_str_len) // 2

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
            COLUMN_GAP,
            " " if lines_are_equal or i > 0 else "|",
            COLUMN_GAP,
            l2,
            sep=""
        )


def main() -> None:
    args = parse_args()

    file1 = read_file(args.file1)
    file2 = read_file(args.file2)

    def get_file_line_by_idx(file: FileContent, line_idx: int) -> str:
        return file.lines[line_idx] if line_idx < file.lines_count else ""

    def compare_lines_func(line1: str, line2: str, ignore_tabs: bool = False) -> bool:
        if ignore_tabs:
            line1 = line1.strip()
            line2 = line2.strip()
        return line1 == line2
    
    compare_lines = partial(compare_lines_func, ignore_tabs=args.ignore_tabs)

    for i in range(max([file1.lines_count, file2.lines_count])):
        line1 = get_file_line_by_idx(file1, i)
        line2 = get_file_line_by_idx(file2, i)

        lines_are_equal = compare_lines(line1, line2)
        print_lines(i, line1, line2, lines_are_equal)


if __name__ == "__main__":
    main()
