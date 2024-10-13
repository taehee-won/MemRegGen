from typing import Final, Dict, Type
from enum import Enum
from argparse import ArgumentParser
from os.path import splitext, basename

from inc import InvalidError, Str, ReadFile, WriteFile
from src.Pkt import PktConfig, PktDef
from src.Pkt import PktGen, PktCHeader, PktDoc


name: Final[str] = "Packet Generator"
version: Final[str] = "v2.0"


class Gen(Enum):
    CHeader = "CHeader"
    Doc = "Doc"


PktGens: Final[Dict[Gen, Type[PktGen]]] = {
    Gen.CHeader: PktCHeader,
    Gen.Doc: PktDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("Gen",    type=str, help="Gen type",        choices=[gen.value for gen in Gen])
    parser.add_argument("PktDef", type=str, help="PktDef file path")
    parser.add_argument("PktGen", type=str, help="PktGen file path")

    parser.add_argument("-n", "--name", default="", type=str, help="packet purpose")

    parser.add_argument("--mask",  default="MASK",  type=str, help="mask name")
    parser.add_argument("--shift", default="SHIFT", type=str, help="shift name")
    parser.add_argument("--raw",   default="RAW",   type=str, help="raw name")

    parser.add_argument("--guard",                       type=str, help="header guard")

    parser.add_argument("--notes", default="", type=lambda s: s.replace('\\n', '\n'), help="notes for headers")

    parser.add_argument("--no-annotation", default=True, help="disable annotation",    action="store_false", dest="annotation")
    parser.add_argument("-d", "--debug",  default=False, help="enable debug messages", action="store_true",  dest="debug")
    # fmt: on

    args = parser.parse_args()

    if args.guard is None:
        args.guard = splitext(basename(args.PktGen))[0].upper()

    Str(f"{name} {version}").add_guard("=").print()

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.PktDef)) != "csv":
        raise InvalidError(
            "File Extension",
            extension,
            f"path({args.PktDef}): pktdef extension should be csv",
        )

    config = PktConfig(args)
    Str(str(config)).insert_guard(".").insert_line("Config").add_guard("-").print()

    pktdef = PktDef(ReadFile(args.PktDef), config)
    if config.debug:
        pktdef.print()

    Str.from_rows(
        [["PktDef", args.PktDef], ["PktGen", args.PktGen]], separator=" : "
    ).insert_guard(".").insert_line("File Paths").add_guard("-").print()

    gen = Gen(args.Gen)
    pktgen = PktGens[gen](pktdef, config)
    pktgen.generate(WriteFile(args.PktGen))

    Str(f"{PktGens[gen].name} Generated").add_guard("=").print()
