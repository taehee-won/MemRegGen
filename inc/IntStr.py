from inc.Exceptions import InvalidIntStrError


class IntStr(str):
    def __new__(cls, value: str):
        if not value.isdigit():
            raise InvalidIntStrError(value)

        return super().__new__(cls, value)
