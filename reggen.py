from typing import Final, Dict, Type
from enum import Enum
from argparse import ArgumentParser
from os.path import splitext, basename

from infos import reggen_name, reggen_version
from inc import InvalidError, Str, ReadFile, WriteFile
from src.Reg import RegConfig, RegDef
from src.Reg import RegGen, RegCHeader, RegVerilogHeader, RegDoc, RegCTestHeader


class Gen(Enum):
    CHeader = "CHeader"
    CTestHeader = "CTestHeader"
    VerilogHeader = "VerilogHeader"
    Doc = "Doc"


RegGens: Final[Dict[Gen, Type[RegGen]]] = {
    Gen.CHeader: RegCHeader,
    Gen.CTestHeader: RegCTestHeader,
    Gen.VerilogHeader: RegVerilogHeader,
    Gen.Doc: RegDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("Gen",    type=str, help="Gen type",        choices=[gen.value for gen in Gen])
    parser.add_argument("RegDef", type=str, help="RegDef file path")
    parser.add_argument("RegGen", type=str, help="RegGen file path")

    parser.add_argument("-n", "--name", default="", type=str, help="IP name")

    parser.add_argument("-r", "--register", default="REG", type=str, help="register name")
    parser.add_argument("-o", "--offset",   default="OFS", type=str, help="offset name")
    parser.add_argument("-m", "--memory",   default="mem", type=str, help="memory address name")

    parser.add_argument("-b", "--bits",  default=32, type=int, help="architecture bits",      choices=[32, 64])
    parser.add_argument("-l", "--align", default=8,  type=int, help="offsets align length", choices=list(range(1, 17)))

    parser.add_argument("--mask",   default="MASK",          type=str, help="mask name")
    parser.add_argument("--shift",  default="SHIFT",         type=str, help="shift name")
    parser.add_argument("--access", default="MEMORY_ACCESS", type=str, help="memory access name")
    parser.add_argument("--reset",  default="RESET_VALUE",   type=str, help="reset value name")
    parser.add_argument("--raw",    default="RAW",           type=str, help="raw name")

    parser.add_argument("--plural",        default="S",   type=str, help="plural ending for address array")
    parser.add_argument("--array",         default="ch",  type=str, help="address array name")
    parser.add_argument("--number",        default="NUM", type=str, help="number name")
    parser.add_argument("--guard",                        type=str, help="header guard")

    parser.add_argument("--notes", default="", type=lambda s: s.replace('\\n', '\n'), help="notes for headers")

    parser.add_argument("--no-annotation", default=True,  help="disable annotation",    action="store_false", dest="annotation")
    parser.add_argument("-d", "--debug",   default=False, help="enable debug messages", action="store_true",  dest="debug")
    # fmt: on

    args = parser.parse_args()

    if args.guard is None:
        args.guard = splitext(basename(args.RegGen))[0].upper()

    Str(f"{reggen_name} {reggen_version}").add_guard("=").print()

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.RegDef)) != "csv":
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.RegDef}): regdef extension should be csv",
        )

    config = RegConfig(args)
    Str(str(config)).insert_guard(".").insert_line("Config").add_guard("-").print()

    regdef = RegDef(ReadFile(args.RegDef), config)
    if config.debug:
        regdef.print()

    Str.from_rows(
        [["Reg Def", args.RegDef], ["Reg Gen", args.RegGen]], separator=" : "
    ).insert_guard(".").insert_line("File Paths").add_guard("-").print()

    gen = Gen(args.Gen)
    reggen = RegGens[gen](regdef, config)
    reggen.generate(WriteFile(args.RegGen))

    Str(f"{RegGens[gen].name} Generated").add_guard("=").print()
