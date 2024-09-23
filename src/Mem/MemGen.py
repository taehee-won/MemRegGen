from abc import ABC, abstractmethod

from inc import WriteFile

from src.Mem.MemConfig import MemConfig
from src.Mem.MemDef import MemDef


class MemGen(ABC):
    name: str = "Memory Generated"

    @abstractmethod
    def __init__(self, memdef: MemDef, config: MemConfig) -> None:
        pass

    @abstractmethod
    def generate(self, file: WriteFile) -> None:
        pass
