from inc.Exceptions import InvalidError


class HexStr(str):
    def __new__(cls, value: str):
        if not cls.is_HexStr(value):
            raise InvalidError("HexStr", value, "impossible to be hexadecimal")

        return super().__new__(cls, value)

    @classmethod
    def is_HexStr(cls, value: str) -> bool:
        return (
            3 <= len(value)
            and value.lower().startswith("0x")
            and all(c in "0123456789abcdefABCDEF" for c in value[2:])
        )

    @classmethod
    def from_int(cls, value: int) -> "HexStr":
        return HexStr(f"0x{value:X}")

    @property
    def value(self) -> int:
        return int(self, 16)

    def get_aligned(self, align: int) -> "HexStr":
        num = self[2:]

        if len(num) < align:
            num = num.zfill(align)

        elif len(num) > align:
            trim = len(num) - align
            if any(c != "0" for c in num[:trim]):
                raise InvalidError("Align", str(align), f"{self} can not be aligned")

            num = num[trim:]

        return HexStr(f"0x{num}")
