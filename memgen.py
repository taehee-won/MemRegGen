from typing import Final, Dict, Type
from enum import Enum
from argparse import ArgumentParser
from os.path import splitext, basename

from infos import memgen_name, memgen_version
from inc import InvalidError, Str, ReadFile, WriteFile
from src.Mem import MemConfig, MemDef
from src.Mem import MemGen, MemCHeader, MemVerilogHeader, MemDoc


class Gen(Enum):
    CHeader = "CHeader"
    VerilogHeader = "VerilogHeader"
    Doc = "Doc"


MemGens: Final[Dict[Gen, Type[MemGen]]] = {
    Gen.CHeader: MemCHeader,
    Gen.VerilogHeader: MemVerilogHeader,
    Gen.Doc: MemDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("Gen",    type=str, help="Gen type",        choices=[gen.value for gen in Gen])
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

    Str(f"{memgen_name} {memgen_version}").add_guard("=").print()

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.MemDef)) != "csv":
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.MemDef}): memdef extension should be csv",
        )

    config = MemConfig(args)
    Str(str(config)).insert_guard(".").insert_line("Config").add_guard("-").print()

    memdef = MemDef(ReadFile(args.MemDef), config)
    if config.debug:
        memdef.print()

    Str.from_rows(
        [["MemDef", args.MemDef], ["MemGen", args.MemGen]], separator=" : "
    ).insert_guard(".").insert_line("File Paths").add_guard("-").print()

    gen = Gen(args.Gen)
    memgen = MemGens[gen](memdef, config)
    memgen.generate(WriteFile(args.MemGen))

    Str(f"{MemGens[gen].name} Generated").add_guard("=").print()
