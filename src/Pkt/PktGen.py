from abc import ABC, abstractmethod

from inc import WriteFile

from src.Pkt.PktConfig import PktConfig
from src.Pkt.PktDef import PktDef


class PktGen(ABC):
    name: str = "Packet Generated"

    @abstractmethod
    def __init__(self, pktdef: PktDef, config: PktConfig) -> None:
        pass

    @abstractmethod
    def generate(self, file: WriteFile) -> None:
        pass
