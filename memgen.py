from typing import Final, Dict, Type
from argparse import ArgumentParser
from os.path import splitext

from inc import InvalidFileExtensionError, Str, ReadFile, WriteFile
from src.Mem import MemConfig, MemDef
from src.Mem import MemGen, MemCHeader, MemVerilogHeader, MemDoc


name: Final[str] = "Memory Generator"
version: Final[str] = "v0.1"


_MemGens: Final[Dict[str, Type[MemGen]]] = {
    "h": MemCHeader,
    "vh": MemVerilogHeader,
    "csv": MemDoc,
}


if __name__ == "__main__":
    parser = ArgumentParser()

    # fmt: off
    parser.add_argument("MemDef",  type=str, help="MemDef file path")
    parser.add_argument("MemGen", type=str, help="MemGen file path")

    parser.add_argument("-g",    "--guard",   type=str,  help="header guard") 
    parser.add_argument("-pre",  "--prefix",  type=str,  help="prefix for definition names")
    parser.add_argument("-post", "--postfix", type=str,  help="postfix for definition names")
    parser.add_argument("-arr",  "--array",   type=str,  help="name for array")
    parser.add_argument("-b",    "--bits",    type=int,  help="bits for architecture")
    parser.add_argument("-l",    "--align",   type=int,  help="align length for addresses")

    parser.add_argument("--alias",    dest="alias", action="store_true",  help="enable alias export")
    parser.add_argument("--no-alias", dest="alias", action="store_false", help="disable alias export")

    parser.add_argument("--debug",    dest="debug", action="store_true",  help="enable debug msgs")
    parser.add_argument("--no-debug", dest="debug", action="store_false", help="disable debug msgs")
    # fmt: on

    args = parser.parse_args()

    print(Str(f"{name} {version}").add_guard("*").contents)

    get_extension = lambda path: splitext(path)[1][1:]

    if (extension := get_extension(args.MemDef)) != "csv":
        raise InvalidFileExtensionError(
            extension, f"path({args.MemDef})" + f": MemDef extension should be csv"
        )

    if (extension := get_extension(args.MemGen)) not in (extensions := _MemGens.keys()):
        raise InvalidFileExtensionError(
            extension,
            f"path({args.MemGen})"
            + f": MemGen extension should be one of these extensions"
            + f": {', '.join(extensions)}",
        )

    config = MemConfig(args)
    if config.debug:
        print(config.debug_str)

    memdef = MemDef(ReadFile(args.MemDef), config)
    if config.debug:
        print(memdef.debug_str)

    memgen = _MemGens[get_extension(args.MemGen)](memdef, config)
    memgen.generate(WriteFile(args.MemGen))
