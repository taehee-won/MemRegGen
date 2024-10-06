from inc.Exceptions import InvalidError


class IntStr(str):
    def __new__(cls, value: str):
        if not cls.is_IntStr(value):
            raise InvalidError("IntStr", value, "impossible to be integer")

        return super().__new__(cls, value)

    @classmethod
    def is_IntStr(cls, value: str) -> bool:
        return value.isdigit()

    @property
    def value(self) -> int:
        return int(self)
