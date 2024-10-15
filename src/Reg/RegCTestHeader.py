from typing import List, Optional, Union

from infos import reggen_name, reggen_version
from inc import WriteFile, Str, HexStr, IntStr

from src.Reg.RegGen import RegGen
from src.Reg.RegConfig import RegConfig
from src.Reg.RegDef import RegDef


class RegCTestHeader(RegGen):
    name: str = "Register C Test Header"

    def __init__(self, regdef: RegDef, config: RegConfig) -> None:
        self._regdef = regdef
        self._config = config

        self._contents = ""

    def generate(self, file: WriteFile) -> None:
        self._append_note_header()
        self._append_open_header_guard()
        self._append_includes()

        self._append_close_header_guard()

        self._write(file)

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
        self._append("#include <test_regs.h>")

    def _append_section_header(self, section: str) -> None:
        self._append("")
        self._append_str(Str(section).add_guard("=").add_prefix("// "))

    def _append_close_header_guard(self) -> None:
        guard = self._config.guard + "_H"

        self._append("")
        self._append(f"#endif // {guard}")

    def _write(self, file: WriteFile) -> None:
        file.write(self._contents)
