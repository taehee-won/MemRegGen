from typing import Final, Dict, Type
from argparse import ArgumentParser
from os.path import splitext, basename

from inc import InvalidFileExtensionError, Str, ReadFile, WriteFile
from src.Mem import MemConfig, MemDef
from src.Mem import MemGen, MemCHeader, MemVerilogHeader, MemDoc


name: Final[str] = "Memory Generator"
version: Final[str] = "v2.2"


_MemGens: Final[Dict[str, Type[MemGen]]] = {
    "h": MemCHeader,
    "vh": MemVerilogHeader,
    "csv": MemDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("MemDef", type=str,  help="MemDef file path")
    parser.add_argument("MemGen", type=str,  help="MemGen file path")

    parser.add_argument("-g",    "--guard",                 type=str,  help="header guard")
    parser.add_argument("-t",    "--type",    default="",   type=str,  help="memory address type")
    parser.add_argument("-pre",  "--prefix",  default="",   type=str,  help="prefix for definition names")
    parser.add_argument("-post", "--postfix", default="",   type=str,  help="postfix for definition names")
    parser.add_argument("-arr",  "--array",   default="ch", type=str,  help="name for array")
    parser.add_argument("-b",    "--bits",    default=64,   type=int,  help="bits for architecture",      choices=[32, 64])
    parser.add_argument("-l",    "--align",                 type=int,  help="align length for addresses", choices=list(range(1, 17)))

    parser.add_argument("--no-annotation", default=True,  help="disable annotation", action="store_false", dest="annotation")
    parser.add_argument("-d", "--debug",   default=False, help="enable debug msgs",  action="store_true",  dest="debug")
    # fmt: on

    args = parser.parse_args()

    if args.guard is None:
        args.guard = splitext(basename(args.MemGen))[0].upper()

    if args.align is None:
        args.align = 16 if getattr(args, "bits") == 64 else 8

    print(Str(f"{name} {version}").add_guard("*").contents)

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.MemDef)) != "csv":
        raise InvalidFileExtensionError(
            extension, f"path({args.MemDef})" + f": memdef extension should be csv"
        )

    if (extension := get_extension(args.MemGen)) not in (extensions := _MemGens.keys()):
        raise InvalidFileExtensionError(
            extension,
            f"path({args.MemGen})"
            + f": memgen extension should be one of these extensions"
            + f": {', '.join(extensions)}",
        )

    config = MemConfig(args)
    if config.debug:
        print(config.debug_str)

    memdef = MemDef(ReadFile(args.MemDef), config)
    if config.debug:
        print(memdef.debug_str)

    print(f"MemDef: {args.MemDef}")
    print(f"MemGen: {args.MemGen}")

    memgen = _MemGens[get_extension(args.MemGen)](memdef, config)
    memgen.generate(WriteFile(args.MemGen))

    print(
        Str(f"{_MemGens[get_extension(args.MemGen)].name} Generated")
        .add_guard("=")
        .contents
    )
