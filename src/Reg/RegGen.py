from abc import ABC, abstractmethod

from inc import WriteFile

from src.Reg.RegConfig import RegConfig
from src.Reg.RegDef import RegDef


class RegGen(ABC):
    name: str = "Register Generated"

    @abstractmethod
    def __init__(self, regdef: RegDef, config: RegConfig) -> None:
        pass

    @abstractmethod
    def generate(self, file: WriteFile) -> None:
        pass
