from typing import List, Optional, Union

from infos import reggen_name, reggen_version
from inc import WriteFile, Str, HexStr, IntStr

from src.Reg.RegGen import RegGen
from src.Reg.RegConfig import RegConfig
from src.Reg.RegDef import RegDef, Offset, Opt


class RegCTestHeader(RegGen):
    name: str = "Register C Test Header"

    def __init__(self, regdef: RegDef, config: RegConfig) -> None:
        self._regdef = regdef
        self._config = config

        self._contents = ""

    def generate(self, file: WriteFile) -> None:
        self._set_offsets()
        self._set_reset_value_config_rows()
        self._set_ro_config_rows()
        self._set_rw_config_rows()
        self._set_row_headers()

        if not self._config.annotation:
            self._remove_annotations()

        self._append_note_header()
        self._append_open_header_guard()
        self._append_includes()

        self._append_reset_value_config_section()
        self._append_ro_config_section()
        self._append_rw_config_section()

        self._append_close_header_guard()

        self._write(file)

    def _set_offsets(self) -> None:
        self._offsets = []

        for offset in self._regdef.offsets:
            self._offsets.append([offset, offset, None])

        for array in self._regdef._arrays:
            for offset in array.offsets:
                for group in array.groups:
                    self._offsets.append(
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

        self._offsets.sort(key=lambda offset: offset[0])

    def _set_reset_value_config_rows(self) -> None:
        self._reset_value_config_rows = []

        for offset, offset_field, array in self._offsets:
            bits = (
                32
                if Opt.Bit32 in offset_field.opts
                else (64 if Opt.Bit64 in offset_field.opts else self._config.bits)
            )

            if any(field.reset is not None for field in offset_field.fields):
                raw = sum(
                    field.reset.value << field.bits[1]
                    for field in offset_field.fields
                    if field.reset is not None
                )
                mask = sum(
                    ((1 << (field.bits[0] - field.bits[1] + 1)) - 1) << field.bits[1]
                    for field in offset_field.fields
                    if field.reset is not None
                )

                self._reset_value_config_rows.append(
                    [
                        "{",
                        f"{self._address(offset.offset)},",
                        f"{str(bits)},",
                        ".raw = { .u" + str(bits) + " =",
                        f"{self._value(raw, bits=bits)}",
                        "},",
                        ".mask = { .u" + str(bits) + " =",
                        f"{self._value(mask, bits=bits)}",
                        "}",
                        "},",
                        "//",
                        (
                            offset.name
                            if array is None
                            else self._join(array.name, offset_field.name)
                        ),  # ID
                        "|",
                        ", ".join(
                            field.name
                            for field in offset_field.fields
                            if field.reset is not None
                        ),  # Field
                        # "|",
                        # ", ".join(
                        #     field.name
                        #     for field in offset_field.fields
                        #     if field.reset is None
                        # ),  # Field(No Reset Value)
                    ]
                )

    def _set_ro_config_rows(self) -> None:
        self._ro_config_rows = []

        for offset, offset_field, array in self._offsets:
            bits = (
                32
                if Opt.Bit32 in offset_field.opts
                else (64 if Opt.Bit64 in offset_field.opts else self._config.bits)
            )

            for field in offset_field.fields:
                if field.access is not None and field.access == "RO":
                    raws = []
                    raws.append(
                        (field.enums[0].val.value << field.bits[1])
                        if field.enums
                        else 0
                    )
                    raws.append(
                        (field.enums[1].val.value << field.bits[1])
                        if 1 < len(field.enums)
                        else (raws[0] + (1 << field.bits[1]))
                    )

                    self._ro_config_rows.append(
                        [
                            "{",
                            f"{self._address(offset.offset)},",
                            f"{str(bits)},",
                            ".write_raws = { { .u" + str(bits) + " =",
                            f"{self._value(raws[0], bits=bits)}",
                            "}, { .u" + str(bits) + " =",
                            f"{self._value(raws[1], bits=bits)}",
                            "} },",
                            ".ro_mask = { .u" + str(bits) + " =",
                            f"{self._value(((1 << (field.bits[0] - field.bits[1] + 1)) - 1) << field.bits[1], bits=bits)}",
                            "} },",
                            "//",
                            (
                                offset.name
                                if array is None
                                else self._join(array.name, offset_field.name)
                            ),  # ID
                            "|",
                            field.name,  # Field
                        ]
                    )

    def _set_rw_config_rows(self) -> None:
        self._rw_config_rows = []

        for offset, offset_field, array in self._offsets:
            bits = (
                32
                if Opt.Bit32 in offset_field.opts
                else (64 if Opt.Bit64 in offset_field.opts else self._config.bits)
            )

            for field in offset_field.fields:
                if field.access is not None and field.access == "RW":
                    raws = []
                    raws.append(
                        (field.enums[0].val.value << field.bits[1])
                        if field.enums
                        else 0
                    )
                    raws.append(
                        (field.enums[1].val.value << field.bits[1])
                        if 1 < len(field.enums)
                        else (raws[0] + (1 << field.bits[1]))
                    )

                    self._rw_config_rows.append(
                        [
                            "{",
                            f"{self._address(offset.offset)},",
                            f"{str(bits)},",
                            ".write_raws = { { .u" + str(bits) + " =",
                            f"{self._value(raws[0], bits=bits)}",
                            "}, { .u" + str(bits) + " =",
                            f"{self._value(raws[1], bits=bits)}",
                            "} },",
                            ".rw_mask = { .u" + str(bits) + " =",
                            f"{self._value(((1 << (field.bits[0] - field.bits[1] + 1)) - 1) << field.bits[1], bits=bits)}",
                            "} },",
                            "//",
                            (
                                offset.name
                                if array is None
                                else self._join(array.name, offset_field.name)
                            ),  # ID
                            "|",
                            field.name,  # Field
                        ]
                    )

    def _set_row_headers(self) -> None:
        if self._reset_value_config_rows:
            self._reset_value_config_rows.insert(
                0,
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "//",
                    "ID",
                    "|",
                    "Field",
                    # "|",
                    # "Field(No Reset Value)",
                ],
            )

            # if all(not row[15] for row in self._reset_value_config_rows[1:]):
            #     for row in self._reset_value_config_rows:
            #         del row[14]
            #         del row[14]

        for rows in [self._ro_config_rows, self._rw_config_rows]:
            rows.insert(
                0,
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "//",
                    "ID",
                    "|",
                    "Field",
                ],
            )

    def _remove_annotations(self) -> None:
        for rows, start in [
            [self._reset_value_config_rows, 10],
            [self._ro_config_rows, 11],
            [self._rw_config_rows, 11],
        ]:
            if rows:
                del rows[0]

            for row in rows:
                for _ in range(start, len(row)):
                    del row[start]

    def _append(self, c: str) -> None:
        self._contents += c + "\n"

    def _append_str(self, s: Str) -> None:
        self._append(str(s))

    def _append_note_header(self) -> None:
        self._append(f"// Do not edit!")
        self._append(f"// This is generated by {reggen_name} {reggen_version}")
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
        self._append("#include <stdint.h>")
        self._append("#include <test_regs.h>")

    def _append_reset_value_config_section(self) -> None:
        if self._reset_value_config_rows:
            self._append("")
            self._append(
                f"struct test_regs_{self._config.reset.lower()}_config test"
                + (f"_{self._config.name.lower()}" if self._config.name else "")
                + f"_regs_{self._config.reset.lower()}_configs[] = "
                + "{"
            )
            self._append_str(
                Str.from_rows(self._reset_value_config_rows).add_prefix("\t")
            )
            self._append("};")

    def _append_ro_config_section(self) -> None:
        if self._ro_config_rows:
            self._append("")
            self._append(
                f"struct test_regs_ro_config test"
                + (f"_{self._config.name.lower()}" if self._config.name else "")
                + f"_regs_ro_configs[] = "
                + "{"
            )
            self._append_str(Str.from_rows(self._ro_config_rows).add_prefix("\t"))
            self._append("};")

    def _append_rw_config_section(self) -> None:
        if self._rw_config_rows:
            self._append("")
            self._append(
                f"struct test_regs_rw_config test"
                + (f"_{self._config.name.lower()}" if self._config.name else "")
                + f"_regs_rw_configs[] = "
                + "{"
            )
            self._append_str(Str.from_rows(self._rw_config_rows).add_prefix("\t"))
            self._append("};")

    def _append_section_header(self, section: str) -> None:
        self._append("")
        self._append_str(Str(section).add_guard("=").add_prefix("// "))

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

    def _value(
        self,
        value: Union[HexStr, IntStr, int],
        bits: Optional[int] = None,
    ) -> str:
        if isinstance(value, IntStr):
            value = HexStr.from_int(value.value)

        elif isinstance(value, int):
            value = HexStr.from_int(value)

        if bits is None:
            bits = self._config.bits

        return (
            f"UL({value.get_aligned(8)})"
            if bits == 32
            else f"ULL({value.get_aligned(16)})"
        )

    def _variable(self, value: str, bits: Optional[int] = None) -> str:
        if bits is None:
            bits = self._config.bits

        return f"uint{bits}_t " + value
