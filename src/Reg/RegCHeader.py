from typing import List, Optional
from reggen import name, version

from inc import WriteFile, Str, HexStr, NotExpectedError

from src.Reg.RegGen import RegGen
from src.Reg.RegConfig import RegConfig
from src.Reg.RegDef import RegDef, Offset, Array


class RegCHeader(RegGen):
    name: str = "Register C Header"

    def __init__(self, regdef: RegDef, config: RegConfig) -> None:
        self._regdef = regdef
        self._config = config

        self._contents = ""

    def generate(self, file: WriteFile) -> None:
        self._set_register_rows()
        self._set_array_rows()
        self._set_field_rows()
        self._set_offset_row_header()

        if not self._config.annotation:
            self._remove_offset_annotation()

        self._append_note_header()
        self._append_open_header_guard()
        self._append_includes()

        self._append_register_section()
        self._append_array_section()
        self._append_field_section()

        self._append_close_header_guard()

        self._write(file)

    def _set_register_rows(self) -> None:
        self._offset_rows = []
        self._register_rows = []

        offsets = []

        for offset in self._regdef.offsets:
            offsets.append([offset, offset, None])

        for array in self._regdef._arrays:
            for offset in array.offsets:
                for group in array.groups:
                    offsets.append(
                        [
                            Offset(
                                f"{array.name}_{offset.name}_{group.name}",
                                HexStr.from_int(
                                    offset.offset.value + group.offset.value
                                ),
                            ),
                            group,
                            array,
                        ]
                    )

        offsets.sort(key=lambda offset: offset[0])

        for offset, offset_field, array in offsets:
            self._offset_rows.append(
                [
                    "#define",
                    self._name(offset.name, tails=[self._config.offset]),
                    f"( {self._address(offset.offset)} )",
                    "//",
                    (
                        offset.name
                        if array is None
                        else f"{array.name}_{offset_field.name}"
                    ),  # Keyword
                    "|",
                    "" if array is None else array.name,  # Array
                    "|",
                    ", ".join(field.name for field in offset_field.fields),  # Fields
                ]
            )

            self._register_rows.append(
                [
                    "#define",
                    self._name(
                        offset.name,
                        tails=[self._config.register],
                        argument=self._config.memory,
                    ),
                    f"( {self._config.memory} + {self._name(offset.name, tails=[self._config.offset])} )",
                    "//",
                    (
                        offset.name
                        if array is None
                        else f"{array.name}_{offset_field.name}"
                    ),  # Keyword
                ]
            )

    def _set_offset_row_header(self) -> None:
        if self._offset_rows:
            self._offset_rows.insert(
                0,
                [
                    "",
                    "",
                    "",
                    "//",
                    "Keyword",
                    "|",
                    "Array",
                    "|",
                    "Field",
                ],
            )

            removed = 0
            for index in range(6, 9, 2):
                if all(not row[index - removed] for row in self._offset_rows[1:]):
                    for row in self._offset_rows:
                        del row[index - removed]  # Field, Array
                        if index != 8:
                            del row[index - removed]  # |

                    removed += 2

    def _remove_offset_annotation(self) -> None:
        del self._offset_rows[0]

        for row in self._offset_rows:
            for _ in range(3, len(row)):
                del row[3]

    def _set_array_rows(self) -> None:
        self._array_num_rows = []
        self._array_register_rows = []
        self._array_step_rows = []

        for array in self._regdef.arrays:
            self._array_num_rows.append(
                [
                    "#define",
                    self._name(
                        array.name,
                        tails=[self._config.array.upper(), self._config.number],
                    ),
                    f"( {array.indexes[-1] + 1} )",
                ]
            )

        for array in self._regdef.arrays:
            for group in array.groups:
                self._array_register_rows.append(
                    [
                        "#define",
                        f"{self._name(f'{array.name}_{group.name}', tails=[self._config.register])}{self._config.plural}({self._config.memory})",
                        "{",
                        ", ".join(
                            (
                                self._name(
                                    f"{array.name}_{index}_{group.name}",
                                    tails=[self._config.register],
                                    argument=self._config.memory,
                                )
                                if index in array.indexes
                                else "NULL"
                            )
                            for index in range(array.indexes[-1] + 1)
                        ),
                        "}",
                    ]
                )

        for array in self._regdef.arrays:
            for group in array.groups:
                if (values := array.step) is not None:
                    base, step, shift = values

                    if shift is not None:
                        self._array_step_rows.append(
                            [
                                "#define",
                                self._name(
                                    f"{array.name}_{group.name}",
                                    tails=[self._config.register],
                                    argument=self._config.array,
                                ),
                                "(",
                                f"{self._address(HexStr.from_int(base.value + group.offset.value))} + ( {self._config.array} << {shift}",
                                ") )",
                            ]
                        )

                    elif step is not None:
                        self._array_step_rows.append(
                            [
                                "#define",
                                self._name(
                                    f"{array.name}_{group.name}",
                                    tails=[self._config.register],
                                    argument=self._config.array,
                                ),
                                "(",
                                f"{self._address(HexStr.from_int(base.value + group.offset.value))} + ( {self._config.array} * {step}",
                                ") )",
                            ]
                        )

                    else:
                        self._array_step_rows.append(
                            [
                                "#define",
                                self._name(
                                    f"{array.name}_{group.name}",
                                    tails=[self._config.register],
                                    argument=self._config.array,
                                ),
                                "(",
                                f"{self._address(HexStr.from_int(array.offsets[0].offset.value + group.offset.value))}",
                                ")",
                                f"// ONLY {array.name}",
                            ]
                        )

                else:
                    self._array_step_rows.append(
                        [
                            "#define",
                            self._name(
                                f"{array.name}_{group.name}",
                                tails=[self._config.register],
                                argument=self._config.array,
                            ),
                            "",
                            "",
                            "",
                            f"// IMPOSSIBLE",
                        ]
                    )

    def _set_field_rows(self) -> None:
        self._field_rows = []

    def _name(
        self,
        name: str,
        tails: List[str] = [],
        argument: Optional[str] = None,
    ) -> str:
        for tail in tails:
            name += f"_{tail}"

        if argument:
            name += f"({argument})"

        return name

    def _address(self, address: HexStr) -> str:
        return address.get_aligned(self._config.align)

    def _append(self, c: str) -> None:
        self._contents += c + "\n"

    def _append_str(self, s: Str) -> None:
        self._append(str(s))

    def _append_note_header(self) -> None:
        self._append(f"// Do not edit!")
        self._append(f"// This is generated by {name} {version}")
        self._append(f"// RegDef hash({self._regdef.file.hash})")

        if self._config.notes:
            self._append("")
            self._append_str(Str(self._config.notes).add_prefix("// "))

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

    def _append_register_section(self) -> None:
        if self._offset_rows:
            self._append("")
            self._append_str(Str.from_rows(self._offset_rows))

        if self._register_rows:
            self._append("")
            self._append_str(Str.from_rows(self._register_rows))

    def _append_array_section(self) -> None:
        parts = [self._array_num_rows, self._array_register_rows, self._array_step_rows]

        if any(parts):
            self._append_section_header("Array Section")

        for rows in parts:
            if rows:
                self._append("")
                self._append_str(Str.from_rows(rows))

    def _append_field_section(self) -> None:
        pass

    def _append_close_header_guard(self) -> None:
        guard = self._config.guard + "_H"

        self._append("")
        self._append(f"#endif // {guard}")

    def _write(self, file: WriteFile) -> None:
        file.write(self._contents)
