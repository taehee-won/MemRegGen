from inc.WriteFile import WriteFile

from src.Reg.RegGen import RegGen
from src.Reg.RegConfig import RegConfig
from src.Reg.RegDef import RegDef


class RegDoc(RegGen):
    name: str = "Register Document"

    def __init__(self, regdef: RegDef, config: RegConfig) -> None:
        raise NotImplementedError()

    def generate(self, file: WriteFile) -> None:
        raise NotImplementedError()
