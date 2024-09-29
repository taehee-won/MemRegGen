from typing import List

from memgen import name, version

from inc import WriteFile, Str, HexStr, NotExpectedError

from src.Mem.MemGen import MemGen
from src.Mem.MemConfig import MemConfig
from src.Mem.MemDef import MemDef, Address, Array


class MemCHeader(MemGen):
    name: str = "Memory C Header"

    def __init__(self, memdef: MemDef, config: MemConfig) -> None:
        self._memdef = memdef
        self._config = config

        self._contents = ""

    def generate(self, file: WriteFile) -> None:
        self._set_address_rows()
        self._set_array_rows()
        self._set_alias_rows()
        self._set_bookmark_rows()

        self._append_note_header()
        self._append_open_header_guard()
        self._append_includes()

        self._append_address_section()
        self._append_array_section()
        self._append_alias_section()
        self._append_bookmark_section()

        self._append_close_header_guard()

        self._write(file)

    def _set_address_rows(self) -> None:
        self._address_rows = []

        for address in self._memdef.addresses:
            self._address_rows.append(
                [
                    "#define",
                    self._name(address.name),
                    address.address,
                    "",
                ]
            )

        for array in self._memdef.arrays:
            for address in array.addresses:
                self._address_rows.append(
                    [
                        "#define",
                        self._name(address.name),
                        address.address,
                        f"// {self._name(array.name)}",  # ({self._config.array})
                    ]
                )

        self._address_rows.sort(key=lambda row: row[2].value)

        for row in self._address_rows:
            row[2] = self._address(row[2])

    def _set_array_rows(self) -> None:
        self._array_num_rows = []
        self._array_rows = []
        self._array_step_rows = []

        for array in self._memdef.arrays:
            self._array_num_rows.append(
                [
                    "#define",
                    f"{self._name(array.name)}_NUM",
                    f"( {array.indexes[-1] + 1} )",
                ]
            )

        for array in self._memdef.arrays:
            self._array_rows.append(
                [
                    "#define",
                    f"{self._name(array.name)}S",
                    "{ "
                    + ", ".join(
                        (
                            self._name(array.addresses[array.indexes.index(index)].name)
                            if index in array.indexes
                            else "NULL"
                        )
                        for index in range(array.indexes[-1] + 1)
                    )
                    + " }",
                ]
            )

        for array in self._memdef.arrays:
            if (step_shift := array.step_shift) is not None:
                base, shift = step_shift

                if shift:
                    self._array_step_rows.append(
                        [
                            "#define",
                            f"{self._name(array.name)}({self._config.array})",
                            f"( {self._address(base)} + ( {self._config.array} << {shift} ) )",
                        ]
                    )

                else:
                    self._array_step_rows.append(
                        [
                            "#define",
                            f"{self._name(array.name)}({self._config.array})",
                            f"( {self._address(base)} )",
                            f"// ONLY {self._name(array.addresses[0].name)}",
                        ]
                    )

            else:
                self._array_step_rows.append(
                    [
                        "#define",
                        f"{self._name(array.name)}({self._config.array})",
                        "",
                        "// IMPOSSIBLE",
                    ]
                )

    def _set_alias_rows(self) -> None:
        self._alias_address_rows = []
        self._alias_array_num_rows = []
        self._alias_array_rows = []
        self._alias_array_step_rows = []

        for alias in self._memdef.aliases:
            if type(alias.alias) == Address:
                self._alias_address_rows.append(
                    [
                        "#define",
                        self._name(alias.name),
                        f"( {self._name(alias.alias.name)} )",
                        alias.alias.address,
                    ]
                )

            elif type(alias.alias) == Array:
                for address in alias.alias.addresses:
                    index = Array.get_index(address.name)

                    self._alias_address_rows.append(
                        [
                            "#define",
                            self._name(f"{alias.name}_{index}"),
                            f"( {self._name(address.name)} )",
                            address.address,
                        ]
                    )

                self._alias_array_num_rows.append(
                    [
                        "#define",
                        f"{self._name(alias.name)}_NUM",
                        f"( {self._name(alias.alias.name)}_NUM )",
                    ]
                )

                self._alias_array_rows.append(
                    [
                        "#define",
                        f"{self._name(alias.name)}S",
                        f"( {self._name(alias.alias.name)}S )",
                    ]
                )

                self._alias_array_step_rows.append(
                    [
                        "#define",
                        f"{self._name(alias.name)}({self._config.array})",
                        f"( {self._name(alias.alias.name)}({self._config.array}) )",
                    ]
                )

            else:
                raise NotExpectedError(f"Invalid, Alias({alias.name})")

        self._alias_address_rows.sort(key=lambda row: row[3].value)

        for row in self._alias_address_rows:
            del row[3]

    def _set_bookmark_rows(self) -> None:
        self._bookmark_rows = []

        for bookmark in self._memdef.bookmarks:
            for row in self._address_rows:
                if row[1] == self._name(bookmark.bookmark):
                    if len(row) == 4:
                        row.append(f"// {self._name(bookmark.name)}")

                    else:
                        row[4] += f", {self._name(bookmark.name)}"

                    break

            else:
                raise NotExpectedError(
                    f"Not Exist, Bookmark({self._name(bookmark.bookmark)})"
                )

            self._bookmark_rows.append(
                [
                    "#define",
                    self._name(bookmark.name),
                    self._name(bookmark.bookmark),
                ]
            )

        def bookmark_index(bookmark_row):
            for index, row in enumerate(self._address_rows):
                if row[1] == bookmark_row[2]:
                    return index

            raise NotExpectedError(f"Not Exist, Bookmark({bookmark_row[2]})")

        self._bookmark_rows.sort(key=bookmark_index)

        for bookmark_row in self._bookmark_rows:
            bookmark_row[2] = f"( {bookmark_row[2]} )"

    def _name(self, name: str) -> str:
        return f"{self._config.prefix}{name}{self._config.postfix}"

    def _address(self, address: HexStr) -> str:
        prefix = "UL(" if self._config.bits == 64 else ""
        postfix = ")" if self._config.bits == 64 else ""

        return f"{prefix}{address.get_aligned(self._config.align)}{postfix}"

    def _append(self, c: str) -> None:
        self._contents += c + "\n"

    def _append_str(self, s: Str) -> None:
        self._append(s.contents)

    def _append_note_header(self) -> None:
        self._append(f"// Do not edit!")
        self._append(f"// This is generated by {name} {version}")
        self._append(f"// MemDef hash({self._memdef.file.hash})")

    def _append_open_header_guard(self) -> None:
        guard = self._config.guard + "_H"

        self._append("")
        self._append(f"#ifndef {guard}")
        self._append(f"#define {guard}")

    def _append_includes(self) -> None:
        self._append("")
        self._append("#include <const.h>")

    def _append_section_header(self, section: str) -> None:
        self._append("")
        self._append_str(Str(section).add_guard("=").add_prefix("// "))

    def _append_address_section(self) -> None:
        self._append_section_header("Address Section")

        if self._address_rows:
            self._append("")
            self._append_str(Str.from_rows(self._address_rows))

    def _append_array_section(self) -> None:
        self._append_section_header("Array Section")

        for rows in [self._array_num_rows, self._array_rows, self._array_step_rows]:
            if rows:
                self._append("")
                self._append_str(Str.from_rows(rows))

    def _append_alias_section(self) -> None:
        self._append_section_header("Alias Section")

        for rows in [
            self._alias_address_rows,
            self._alias_array_num_rows,
            self._alias_array_rows,
            self._alias_array_step_rows,
        ]:
            if rows:
                self._append("")
                self._append_str(Str.from_rows(rows))

    def _append_bookmark_section(self) -> None:
        self._append_section_header("Bookmark Section")

        if self._bookmark_rows:
            self._append("")
            self._append_str(Str.from_rows(self._bookmark_rows))

    def _append_close_header_guard(self) -> None:
        guard = self._config.guard + "_H"

        self._append("")
        self._append(f"#endif // {guard}")

    def _write(self, file: WriteFile) -> None:
        file.write(self._contents)
