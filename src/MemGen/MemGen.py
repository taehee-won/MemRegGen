from abc import ABC, abstractmethod

from inc import WriteFile

from src.MemGen.MemConfig import MemConfig
from src.MemGen.MemDef import MemDef


class MemGen(ABC):
    name: str = "Memory Generated"

    @abstractmethod
    def __init__(self, memdef: MemDef, config: MemConfig) -> None:
        pass

    @abstractmethod
    def generate(self, file: WriteFile) -> None:
        pass
