from inc.WriteFile import WriteFile

from src.Mem.MemGen import MemGen
from src.Mem.MemConfig import MemConfig
from src.Mem.MemDef import MemDef


class MemDoc(MemGen):
    name: str = "Memory Document"

    def __init__(self, memdef: MemDef, config: MemConfig) -> None:
        raise NotImplementedError()

    def generate(self, file: WriteFile) -> None:
        raise NotImplementedError()
