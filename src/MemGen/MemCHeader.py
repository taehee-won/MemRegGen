from inc.WriteFile import WriteFile

from src.MemGen.MemGen import MemGen
from src.MemGen.MemConfig import MemConfig
from src.MemGen.MemDef import MemDef


class MemCHeader(MemGen):
    name: str = "Memory C Header"

    def __init__(self, memdef: MemDef, config: MemConfig) -> None:
        raise NotImplementedError()

    def generate(self, file: WriteFile) -> None:
        raise NotImplementedError()
