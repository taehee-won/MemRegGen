from typing import List, Union


class Str:
    def __init__(self, contents: str) -> None:
        self._contents = contents

    def __add__(self, other: Union["Str", str]) -> "Str":
        return Str(
            self._contents + (other.contents if isinstance(other, Str) else other)
        )

    @classmethod
    def from_rows(cls, rows: List[List[str]], separator: str = " ") -> "Str":
        if not rows:
            return cls("")

        nums = max(len(row) for row in rows)
        for row in rows:
            if len(row) < nums:
                row.extend(["" for _ in range(0, nums - len(row))])

        columns = len(rows[0])
        widths = [max(len(row[index]) for row in rows) for index in range(columns)]

        aligned_rows = [
            separator.join(
                row[index].ljust(widths[index]) if index < columns - 1 else row[index]
                for index in range(columns)
            ).rstrip()
            for row in rows
        ]

        return cls("\n".join(aligned_rows))

    def print(self) -> None:
        print(self._contents)

    def append(self, other: "Str") -> "Str":
        self._contents += "\n" + other._contents

        return self

    # TODO: when contents is empty string, max([]) or width - len(prefix) could be issue

    def insert_guard(self, guard: str, prefix: str = "") -> "Str":
        width = max(len(line) for line in self._contents.split("\n"))
        width -= len(prefix)

        line = prefix + (guard * width)
        self._contents = "\n".join([line, self._contents])

        return self

    def add_guard(self, guard: str, prefix: str = "") -> "Str":
        width = max(len(line) for line in self._contents.split("\n"))
        width -= len(prefix)

        line = prefix + (guard * width)
        self._contents = "\n".join([line, self._contents, line])

        return self

    def insert_line(self, line: str, prefix: str = "") -> "Str":
        self._contents = "\n".join([prefix + line, self._contents])

        return self

    def append_line(self, line: str, prefix: str = "") -> "Str":
        self._contents = "\n".join([self._contents, prefix + line])

        return self

    def add_prefix(self, prefix: str = "") -> "Str":
        self._contents = "\n".join(prefix + line for line in self._contents.split("\n"))

        return self

    def __str__(self) -> str:
        return self._contents

    @property
    def contents(self) -> str:
        return self._contents
