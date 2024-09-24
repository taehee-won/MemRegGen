from inc.Exceptions import InvalidHexStrError, InvalidAlignError


class HexStr(str):
    def __new__(cls, value: str):
        value = value.lower()

        if not (
            3 <= len(value)
            and value.lower().startswith("0x")
            and all(c in "0123456789abcdef" for c in value[2:])
        ):
            raise InvalidHexStrError(value)

        return super().__new__(cls, value)

    @classmethod
    def from_int(cls, value: int) -> "HexStr":
        return HexStr(f"0x{value}:X")

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
                raise InvalidAlignError(align, self)

            num = num[trim:]

        return HexStr(f"0x{num}")
