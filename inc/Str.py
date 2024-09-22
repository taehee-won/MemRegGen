from typing import List

from inc.Exceptions import InvalidRowColumnError


class Str:
    def __init__(self, contents: str) -> None:
        self._contents = contents

    @classmethod
    def from_rows(cls, rows: List[List[str]], separator: str = " ") -> "Str":
        if len(set(len(row) for row in rows)) != 1:
            raise InvalidRowColumnError("all rows must have the same number of columns")

        columns = len(rows[0])
        widths = [max(len(row[index]) for row in rows) for index in range(columns)]

        aligned_rows = [
            separator.join(
                row[index].ljust(widths[index]) if index < columns - 1 else row[index]
                for index in range(columns)
            )
            for row in rows
        ]

        return cls("\n".join(aligned_rows))

    def insert_guard(self, guard: str) -> "Str":
        line = guard * max(len(line) for line in self._contents.split("\n"))

        self._contents = "\n".join([line, self._contents])

        return self

    def add_guard(self, guard: str) -> "Str":
        line = guard * max(len(line) for line in self._contents.split("\n"))

        self._contents = "\n".join([line, self._contents, line])

        return self

    def insert_line(self, line: str) -> "Str":
        self._contents = "\n".join([line, self._contents])

        return self

    def append_line(self, line: str) -> "Str":
        self._contents = "\n".join([self._contents, line])

        return self

    def add_prefix(self, prefix: str = "    ") -> "Str":
        self._contents = "\n".join(prefix + line for line in self._contents.split("\n"))

        return self

    def __str__(self) -> str:
        return self._contents

    @property
    def contents(self) -> str:
        return self._contents
