from typing import Final, Dict, Type
from argparse import ArgumentParser
from os.path import splitext, basename

from inc import InvalidError, Str, ReadFile, WriteFile
from src.Mem import MemConfig, MemDef
from src.Mem import MemGen, MemCHeader, MemVerilogHeader, MemDoc


name: Final[str] = "Memory Generator"
version: Final[str] = "v4.3"


_MemGens: Final[Dict[str, Type[MemGen]]] = {
    "h": MemCHeader,
    "vh": MemVerilogHeader,
    "csv": MemDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("MemDef", type=str, help="MemDef file path")
    parser.add_argument("MemGen", type=str, help="MemGen file path")

    parser.add_argument("-m", "--memory", default="MEM", type=str, help="memory address name")

    parser.add_argument("-b", "--bits",  default=64, type=int, help="architecture bits",      choices=[32, 64])
    parser.add_argument("-l", "--align",             type=int, help="addresses align length", choices=list(range(1, 17)))

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
        args.guard = splitext(basename(args.MemGen))[0].upper()

    if args.align is None:
        args.align = 16 if getattr(args, "bits") == 64 else 8

    Str(f"{name} {version}").add_guard("=").print()

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.MemDef)) != "csv":
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.MemDef}): memdef extension should be csv",
        )

    if (extension := get_extension(args.MemGen)) not in (extensions := _MemGens.keys()):
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.MemGen}): memgen extension should be one of these extensions"
            + f": {', '.join(extensions)}",
        )

    config = MemConfig(args)
    Str(str(config)).insert_guard(".").insert_line("Config").add_guard("-").print()

    memdef = MemDef(ReadFile(args.MemDef), config)
    if config.debug:
        memdef.print()

    Str.from_rows(
        [["MemDef", args.MemDef], ["MemGen", args.MemGen]], separator=" : "
    ).insert_guard(".").insert_line("File Paths").add_guard("-").print()

    memgen = _MemGens[get_extension(args.MemGen)](memdef, config)
    memgen.generate(WriteFile(args.MemGen))

    Str(f"{_MemGens[get_extension(args.MemGen)].name} Generated").add_guard("=").print()
