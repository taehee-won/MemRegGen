from inc.WriteFile import WriteFile

from src.Pkt.PktGen import PktGen
from src.Pkt.PktConfig import PktConfig
from src.Pkt.PktDef import PktDef


class PktCHeader(PktGen):
    name: str = "Packet C Header"

    def __init__(self, pktdef: PktDef, config: PktConfig) -> None:
        raise NotImplementedError()

    def generate(self, file: WriteFile) -> None:
        raise NotImplementedError()
