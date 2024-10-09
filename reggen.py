from typing import Final, Dict, Type
from argparse import ArgumentParser
from os.path import splitext, basename

from inc import InvalidError, Str, ReadFile, WriteFile
from src.Reg import RegConfig, RegDef
from src.Reg import RegGen, RegCHeader, RegVerilogHeader, RegDoc


name: Final[str] = "Register Generator"
version: Final[str] = "v0.1"


_RegGens: Final[Dict[str, Type[RegGen]]] = {
    "h": RegCHeader,
    "vh": RegVerilogHeader,
    "csv": RegDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("RegDef", type=str, help="RegDef file path")
    parser.add_argument("RegGen", type=str, help="RegGen file path")

    parser.add_argument("-n", "--name", default="", type=str, help="IP name")

    parser.add_argument("-r", "--register", default="REG", type=str, help="register name")
    parser.add_argument("-o", "--offset",   default="OFS", type=str, help="offset name")
    parser.add_argument("-m", "--memory",   default="mem", type=str, help="memory address name")

    parser.add_argument("-b", "--bits",  default=64, type=int, help="architecture bits",      choices=[32, 64])
    parser.add_argument("-l", "--align",             type=int, help="addresses align length", choices=list(range(1, 17)))

    parser.add_argument("--mask",   default="MASK",  type=str, help="mask name")
    parser.add_argument("--shift",  default="SHIFT", type=str, help="shift name")
    parser.add_argument("--access", default="ACCESS", type=str, help="memory access name")
    parser.add_argument("--reset",  default="RESET",  type=str, help="reset value name")
    parser.add_argument("--raw",    default="RAW",   type=str, help="raw name")

    parser.add_argument("--plural",        default="S",   type=str, help="plural ending for address array")
    parser.add_argument("--array",         default="ch",  type=str, help="address array name")
    parser.add_argument("--number",        default="NUM", type=str, help="number name")
    parser.add_argument("--guard",                        type=str, help="header guard")
    parser.add_argument("--no-annotation", default=True,            help="disable annotation", action="store_false", dest="annotation")

    parser.add_argument("-d", "--debug", default=False, help="enable debug messages", action="store_true", dest="debug")
    # fmt: on

    args = parser.parse_args()

    if args.guard is None:
        args.guard = splitext(basename(args.RegGen))[0].upper()

    if args.align is None:
        args.align = 16 if getattr(args, "bits") == 64 else 8

    Str(f"{name} {version}").add_guard("=").print()

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.RegDef)) != "csv":
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.RegDef}): regdef extension should be csv",
        )

    if (extension := get_extension(args.RegGen)) not in (extensions := _RegGens.keys()):
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.RegGen}): reggen extension should be one of these extensions"
            + f": {', '.join(extensions)}",
        )

    config = RegConfig(args)
    Str(str(config)).insert_guard(".").insert_line("Config").add_guard("-").print()

    regdef = RegDef(ReadFile(args.RegDef), config)
    if config.debug:
        regdef.print()

    Str.from_rows(
        [["Reg Def", args.RegDef], ["Reg Gen", args.RegGen]], separator=" : "
    ).insert_guard(".").insert_line("File Paths").add_guard("-").print()

    reggen = _RegGens[get_extension(args.RegGen)](regdef, config)
    reggen.generate(WriteFile(args.RegGen))

    Str(f"{_RegGens[get_extension(args.RegGen)].name} Generated").add_guard("=").print()
