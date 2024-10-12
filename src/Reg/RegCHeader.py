from typing import List, Optional, Union
from reggen import name, version

from inc import WriteFile, Str, HexStr, IntStr

from src.Reg.RegGen import RegGen
from src.Reg.RegConfig import RegConfig
from src.Reg.RegDef import RegDef, Offset


class RegCHeader(RegGen):
    name: str = "Register C Header"

    def __init__(self, regdef: RegDef, config: RegConfig) -> None:
        self._regdef = regdef
        self._config = config

        self._contents = ""

    def generate(self, file: WriteFile) -> None:
        self._set_register_rows()
        self._set_array_rows()
        self._set_offset_group_items()
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
                                self._join(array.name, offset.name, group.name),
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
                        else self._join(array.name, offset_field.name)
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
                        else self._join(array.name, offset_field.name)
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
                    "ID",
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
                        f"{self._name(self._join(array.name, group.name), tails=[self._config.register])}{self._config.plural}({self._config.memory})",
                        "{",
                        ", ".join(
                            (
                                self._name(
                                    self._join(array.name, str(index), group.name),
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
                                    self._join(array.name, group.name),
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
                                    self._join(array.name, group.name),
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
                                    self._join(array.name, group.name),
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
                                self._join(array.name, group.name),
                                tails=[self._config.register],
                                argument=self._config.array,
                            ),
                            "",
                            "",
                            "",
                            f"// IMPOSSIBLE",
                        ]
                    )

    def _set_offset_group_items(self) -> None:
        self._items = []

        for offset in self._regdef.offsets:
            self._items.append([None, offset, offset.offset.value])

        for array in self._regdef._arrays:
            for group in array.groups:
                self._items.append(
                    [
                        array,
                        group,
                        (
                            array.offsets[0].offset.value
                            if array.offsets
                            else 0xFFFFFFFFFFFFFFFF
                        ),
                    ]
                )

        self._items.sort(key=lambda offset: offset[2])

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

        self._append("")
        self._append("#ifndef __ASSEMBLY__")
        self._append("#include <stdint.h> // for union")
        self._append("#endif")

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
        if self._items:
            for item in self._items:
                name = (
                    item[1].name
                    if item[0] is None
                    else self._join(item[0].name, item[1].name)
                )
                section = name + (
                    f" : {', '.join(field.name for field in item[1].fields)}"
                    if item[1].fields
                    else ""
                )

                self._append_section_header(section)

                if item[1].fields:
                    self._append("")
                    self._append("#ifndef __ASSEMBLY__")

                    union = Str(f"union {name} " + "{")
                    union.append_line(f"\t{self._variable("raw")};")
                    union.append_line("")
                    union.append_line("\tstruct {")

                    rows = []

                    curr = 0
                    reserved = 0
                    for field in item[1].fields:
                        start = field.bits[1]
                        end = field.bits[0]

                        if curr != start:
                            rows.append([f"RSVD{reserved}", str(start - curr)])
                            reserved += 1

                        rows.append([field.name, end - start + 1])

                        curr = end + 1

                    if curr != self._config.bits:
                        rows.append([f"RSVD{reserved}", str(self._config.bits - curr)])

                    print(rows)
                    union.append(
                        Str.from_rows(
                            [
                                [self._variable(row[0]), ":", str(row[1]) + ";"]
                                for row in rows
                            ]
                        ).add_prefix("\t\t")
                    )

                    union.append_line("\t};")
                    union.append_line("};")

                    self._append_str(union)
                    self._append("#endif")

                    for field in item[1].fields:
                        field_name = self._join(name, field.name)
                        self._append("")
                        self._append(f"// {self._name(field_name)}")

                        self._append("")
                        self._append_str(
                            Str.from_rows(
                                [
                                    [
                                        "#define",
                                        self._name(
                                            field_name, tails=[self._config.mask]
                                        ),
                                        self._value(
                                            (1 << (field.bits[0] - field.bits[1] + 1))
                                            - 1
                                        ),
                                    ],
                                    [
                                        "#define",
                                        self._name(
                                            field_name, tails=[self._config.shift]
                                        ),
                                        f"( {field.bits[1]} )",
                                    ],
                                ]
                            )
                        )

                        if field.enums:
                            self._append("")
                            self._append_str(
                                Str.from_rows(
                                    [
                                        [
                                            "#define",
                                            self._name(
                                                self._join(field_name, enum.name)
                                            ),
                                            f"( {enum.val.value} )",
                                        ]
                                        for enum in field.enums
                                    ]
                                )
                            )

                            self._append("")
                            self._append_str(
                                Str.from_rows(
                                    [
                                        [
                                            "#define",
                                            self._name(
                                                self._join(field_name, enum.name),
                                                tails=[self._config.raw],
                                            ),
                                            self._value(
                                                enum.val.value << field.bits[1]
                                            ),
                                        ]
                                        for enum in field.enums
                                    ]
                                )
                            )

                    self._append("")
                    self._append(f"// {self._name(name, tails=[self._config.raw])}")

                    self._append("")
                    self._append_str(
                        Str.from_rows(
                            [
                                [
                                    "#define",
                                    f"{self._name(self._join(name, field.name), tails=[self._config.raw])}({field.name.lower()})",
                                    f"( ( {field.name.lower()}",
                                    "&",
                                    self._name(
                                        self._join(name, field.name),
                                        tails=[self._config.mask],
                                    ),
                                    ") <<",
                                    self._name(
                                        self._join(name, field.name),
                                        tails=[self._config.shift],
                                    ),
                                    ")",
                                ]
                                for field in item[1].fields
                            ]
                        )
                    )

                    self._append("")
                    self._append(
                        f"#define {self._name(name, tails=[self._config.raw])}"
                        + f"({', '.join(field.name.lower() for field in item[1].fields)})"
                        + f" ( {' | '.join(f'{self._name(self._join(name, field.name), tails=[self._config.raw])}({field.name.lower()})' for field in item[1].fields)} )"
                    )

                else:
                    self._append("")
                    self._append(
                        f"// {self._name(name, tails=[self._config.raw])} : NO FIELD"
                    )

                    self._append("")
                    self._append_str(
                        Str.from_rows(
                            [
                                [
                                    "#define",
                                    f"{self._name(name, tails=[self._config.raw])}()",
                                    self._value(0),
                                ]
                            ]
                        )
                    )

    def _append_close_header_guard(self) -> None:
        guard = self._config.guard + "_H"

        self._append("")
        self._append(f"#endif // {guard}")

    def _write(self, file: WriteFile) -> None:
        file.write(self._contents)

    def _join(self, *tokens) -> str:
        return "_".join(tokens)

    def _name(
        self,
        name: str,
        tails: List[str] = [],
        argument: Optional[str] = None,
    ) -> str:
        if self._config.name:
            name = f"{self._config.name}_{name}"

        for tail in tails:
            name += f"_{tail}"

        if argument:
            name += f"({argument})"

        return name

    def _address(self, address: HexStr) -> str:
        return address.get_aligned(self._config.align)

    def _value(self, value: Union[HexStr, IntStr, int]) -> str:
        if isinstance(value, IntStr):
            value = HexStr.from_int(value.value)

        elif isinstance(value, int):
            value = HexStr.from_int(value)

        return (
            f"UL({value.get_aligned(8)})"
            if self._config.bits == 32
            else f"ULL({value.get_aligned(16)})"
        )

    def _variable(self, value: str) -> str:
        return f"uint{self._config.bits}_t " + value
