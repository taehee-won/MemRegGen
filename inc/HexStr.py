from inc.Exceptions import InvalidHexStrError


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
